"""One-click CV sync for davidawoyemi.net.

Finds the newest CV in the job-materials folder (or uses a file dropped onto
the launcher), shows what would change, copies it into the repository,
rebuilds the site, commits, and pushes. GitHub Actions then deploys.

Usage:
    python scripts/sync_cv.py                 # newest CV under the configured folder
    python scripts/sync_cv.py path/to/CV.docx # a specific file (drag-and-drop)
    python scripts/sync_cv.py --dry-run       # preview only, change nothing
    python scripts/sync_cv.py --yes           # skip the confirmation prompt
    python scripts/sync_cv.py --no-push       # commit locally, do not push

Configuration lives in scripts/sync_cv.config.json (ignored by git):
    {
      "search_root": "C:\\path\\to\\job materials folder",
      "file_name": "David_CV.docx",
      "strip_phone": false
    }
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
CONFIG_PATH = SCRIPTS / "sync_cv.config.json"
DEFAULT_CONFIG = {"search_root": "", "file_name": "David_CV.docx", "strip_phone": False}
REQUIRED_SECTIONS = ("EDUCATION", "PUBLICATIONS", "RESEARCH EXPERIENCE", "GRANTS")
# A US phone number such as (659) 228-4351 or 659-228-4351. The look-arounds
# keep it from matching digit runs inside DOIs, grant amounts, or ISBNs.
PHONE_RE = re.compile(r"(?<![\d.])(?:\(\d{3}\)\s*|\d{3}[-.\s])\d{3}[-.\s]\d{4}(?![\d.])")

sys.path.insert(0, str(SCRIPTS))
import build_site  # noqa: E402  (the site generator; provides the docx parser)


# --------------------------------------------------------------------------- helpers
def say(message: str = "") -> None:
    print(message, flush=True)


def fail(message: str) -> None:
    say(f"\nERROR: {message}")
    sys.exit(1)


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        CONFIG_PATH.write_text(json.dumps(DEFAULT_CONFIG, indent=2), encoding="utf-8")
        return dict(DEFAULT_CONFIG)
    config = dict(DEFAULT_CONFIG)
    config.update(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
    return config


def find_source(explicit: str | None, config: dict) -> Path:
    if explicit:
        path = Path(explicit).expanduser()
        if not path.is_file():
            fail(f"File not found: {path}")
        if path.suffix.lower() != ".docx":
            fail(f"Expected a .docx file, got: {path.name}")
        return path
    root = Path(config.get("search_root") or "")
    if not str(root) or not root.is_dir():
        fail(
            "No CV given and no valid search folder configured.\n"
            f"Set \"search_root\" in {CONFIG_PATH} to your job-materials folder,\n"
            "or drop the CV file onto the launcher."
        )
    name = config.get("file_name") or DEFAULT_CONFIG["file_name"]
    candidates = [p for p in root.rglob(name) if not p.name.startswith("~$")]
    if not candidates:
        fail(f"No file named {name} found under {root}")
    return max(candidates, key=lambda p: p.stat().st_mtime)


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(path: Path) -> dict[str, int]:
    paragraphs = build_site.read_docx_paragraphs(path)
    _header, sections = build_site.split_sections(paragraphs)
    return {key: len(lines) for key, lines in sections.items()}


def preview_metrics(path: Path) -> dict[str, int]:
    """Build the site data in memory from `path` and return the headline metrics."""
    original = build_site.SOURCE_DOCX
    build_site.SOURCE_DOCX = path
    try:
        data = build_site.build_site_data()
    finally:
        build_site.SOURCE_DOCX = original
    return {item["label"]: item["value"] for item in data["metrics"]}


def current_metrics() -> dict[str, int]:
    site_data = ROOT / "site-data.json"
    if not site_data.exists():
        return {}
    data = json.loads(site_data.read_text(encoding="utf-8"))
    return {item["label"]: item["value"] for item in data.get("metrics", [])}


def strip_phone(path: Path) -> str | None:
    """Remove the phone number from the contact line of the copied CV.

    Only the contact block at the top of the document is touched (the line
    that also carries the email address), so referees' numbers stay intact.
    Characters are cut from the individual text nodes rather than rewriting
    the paragraph, which preserves hyperlinks and formatting.
    Returns the removed phone number, or None if nothing changed.
    """
    import docx  # python-docx, imported lazily so the sync works without it when disabled
    from docx.oxml.ns import qn

    document = docx.Document(str(path))
    removed = None
    for paragraph in document.paragraphs[:12]:
        nodes = list(paragraph._p.iter(qn("w:t")))
        full = "".join(node.text or "" for node in nodes)
        if "@" not in full or not PHONE_RE.search(full):
            continue
        # Prefer removing the separator with the number: "a | (659) 228-4351 | b" -> "a | b".
        match = re.search(r"\s*\|\s*" + PHONE_RE.pattern + r"(?=\s*(?:\||$))", full) or PHONE_RE.search(full)
        start, end = match.span()
        removed = PHONE_RE.search(match.group(0)).group(0)
        offset = 0
        for node in nodes:
            text = node.text or ""
            node_start, node_end = offset, offset + len(text)
            offset = node_end
            if node_end <= start or node_start >= end:
                continue
            cut_from = max(start, node_start) - node_start
            cut_to = min(end, node_end) - node_start
            node.text = text[:cut_from] + text[cut_to:]
            node.set(qn("xml:space"), "preserve")
        break
    if removed:
        document.save(str(path))
    return removed


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True)
    if check and result.returncode != 0:
        fail(f"git {' '.join(args)} failed:\n{result.stderr.strip() or result.stdout.strip()}")
    return result


def actions_url() -> str:
    remote = git("remote", "get-url", "origin", check=False).stdout.strip()
    remote = re.sub(r"\.git$", "", remote)
    remote = re.sub(r"^git@github\.com:", "https://github.com/", remote)
    return f"{remote}/actions" if remote.startswith("http") else ""


# --------------------------------------------------------------------------- main
def main() -> None:
    parser = argparse.ArgumentParser(description="Publish the latest CV to the website.")
    parser.add_argument("source", nargs="?", help="CV file to publish (default: newest in the configured folder)")
    parser.add_argument("--yes", "-y", action="store_true", help="do not ask for confirmation")
    parser.add_argument("--dry-run", action="store_true", help="show what would change and stop")
    parser.add_argument("--no-push", action="store_true", help="commit but do not push")
    parser.add_argument("--strip-phone", dest="strip_phone", action="store_true", default=None,
                        help="remove the phone number from the published copy")
    parser.add_argument("--keep-phone", dest="strip_phone", action="store_false",
                        help="keep the phone number even if the config says to strip it")
    args = parser.parse_args()

    config = load_config()
    strip = config.get("strip_phone", False) if args.strip_phone is None else args.strip_phone

    source = find_source(args.source, config)
    target = ROOT / build_site.SOURCE_DOCX.name
    modified = date.fromtimestamp(source.stat().st_mtime).isoformat()
    say("CV to publish")
    say(f"  file:      {source}")
    say(f"  modified:  {modified}")
    say(f"  website:   {target.name}")

    if target.exists() and file_hash(source) == file_hash(target):
        say("\nThe website already has this exact CV. Nothing to do.")
        return

    # Parse the new file and compare with the current one before touching anything.
    try:
        new_sections = summarize(source)
    except Exception as error:  # noqa: BLE001 - report any parse failure plainly
        fail(f"Could not read the CV: {error}")
    missing = [name for name in REQUIRED_SECTIONS if name not in new_sections]
    if missing:
        fail("The CV is missing sections the website needs: " + ", ".join(missing)
             + "\nCheck the headings in the document; expected headings are listed in scripts/build_site.py.")

    old_sections = summarize(target) if target.exists() else {}
    say("\nSection changes (lines in each CV section)")
    changed_any = False
    for key in sorted(set(old_sections) | set(new_sections)):
        before, after = old_sections.get(key, 0), new_sections.get(key, 0)
        if before != after:
            changed_any = True
            say(f"  {key:<40} {before:>4} -> {after:<4}")
    if not changed_any:
        say("  (same line counts; wording changes only)")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_copy = Path(temp_dir) / target.name
        shutil.copy2(source, temp_copy)
        try:
            new_metrics = preview_metrics(temp_copy)
        except Exception as error:  # noqa: BLE001
            fail(f"The website generator could not process this CV: {error}")
    old_metrics = current_metrics()
    say("\nHomepage metrics")
    for label, value in new_metrics.items():
        before = old_metrics.get(label)
        marker = "" if before == value else f"   (was {before})"
        say(f"  {label:<26} {value:>4}{marker}")

    if strip:
        say("\nThe phone number will be removed from the published copy.")

    if args.dry_run:
        say("\nDry run: nothing was changed.")
        return
    if not args.yes:
        say("")
        try:
            answer = input("Publish this CV to the website? [Y/n] ").strip().lower()
        except EOFError:
            answer = "n"
        if answer not in ("", "y", "yes"):
            say("Cancelled. Nothing was changed.")
            return

    # Copy, optionally strip the phone number, rebuild.
    shutil.copy2(source, target)
    removed_phone = None
    if strip:
        try:
            removed_phone = strip_phone(target)
        except ImportError:
            fail("python-docx is required for --strip-phone. Install it with: pip install python-docx")
        say("Removed the phone number from the published copy." if removed_phone else "No phone number found to remove.")

    say("\nRebuilding the website ...")
    build = subprocess.run([sys.executable, str(SCRIPTS / "build_site.py")], cwd=ROOT, text=True, capture_output=True)
    if build.returncode != 0:
        fail(f"Build failed:\n{build.stderr.strip() or build.stdout.strip()}")
    say("  " + (build.stdout.strip().splitlines() or ["done"])[-1])

    if removed_phone:
        pages = list(ROOT.glob("*.html")) + [ROOT / "site-data.json"]
        leaked = [p.name for p in pages if removed_phone in p.read_text(encoding="utf-8")]
        if leaked:
            say("  WARNING: the phone number still appears in " + ", ".join(leaked))

    # Commit and push only the CV and the generated pages.
    tracked = [target.name, "site-data.json", *sorted(p.name for p in ROOT.glob("*.html"))]
    git("add", "--", *tracked)
    if git("diff", "--cached", "--quiet", check=False).returncode == 0:
        say("\nNo website changes resulted from this CV. Nothing to commit.")
        return
    message = f"Update CV from job materials ({date.today().isoformat()})"
    git("commit", "-q", "-m", message)
    say(f"\nCommitted: {message}")
    if args.no_push:
        say("Not pushed (--no-push). Run 'git push' when ready.")
        return
    push = git("push", "origin", "HEAD", check=False)
    if push.returncode != 0:
        fail("Push failed. The commit is saved locally; check your connection and run 'git push'.\n"
             + (push.stderr.strip() or push.stdout.strip()))
    say("Pushed. GitHub Actions is deploying the site now (about a minute).")
    url = actions_url()
    if url:
        say(f"Progress: {url}")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except AttributeError:
        pass
    main()
