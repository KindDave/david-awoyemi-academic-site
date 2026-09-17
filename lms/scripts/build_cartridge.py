#!/usr/bin/env python3
"""Build IMS Common Cartridge (1.1) packages and HTML previews from course sources.

Usage:
    python lms/scripts/build_cartridge.py            # build every course in lms/courses
    python lms/scripts/build_cartridge.py <slug>     # build one course

Each course lives in lms/courses/<slug>/ with a course.json that lists modules and
items. Item types: page, assignment, discussion, quiz, link. Page, assignment and
discussion bodies are Markdown files; quizzes are JSON. Output goes to lms/dist/:

    lms/dist/<slug>.imscc                 -> import into Moodle, Canvas, Blackboard
    lms/dist/preview/<slug>/index.html    -> review the whole course in a browser
"""
from __future__ import annotations

import html
import json
import re
import shutil
import sys
import uuid
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COURSES_DIR = ROOT / "courses"
DIST_DIR = ROOT / "dist"
MEDIA_DIR = ROOT / "media"          # generated videos: media/<slug>/<id>.mp4 + .vtt (see make_videos.py)
VIDEOS_DIR = ROOT / "videos"        # video scripts: videos/<slug>/<id>.json

VIDEO_MARKER = re.compile(r"^\s*\{\{\s*video:\s*([\w-]+)\s*\}\}\s*$", re.MULTILINE)
YOUTUBE_MARKER = re.compile(r"^\s*\{\{\s*youtube:\s*([A-Za-z0-9_-]{6,})\s*\|\s*([^|}]+?)\s*(?:\|\s*([^}]+?))?\s*\}\}\s*$", re.MULTILINE)


def youtube_embed(video_id: str, title: str, note: str = "") -> str:
    """Responsive, privacy-enhanced YouTube embed used for the instructor's own recordings."""
    t = html.escape(title)
    n = html.escape(note) if note else "Recorded by the instructor for the 2025 pilot of this program."
    return (f'<figure class="video youtube"><div class="yt-wrap">'
            f'<iframe src="https://www.youtube-nocookie.com/embed/{video_id}?rel=0" title="{t}" width="900" height="506" '
            f'allow="accelerometer; encrypted-media; picture-in-picture" allowfullscreen loading="lazy"></iframe></div>'
            f'<figcaption><strong>{t}.</strong> {n}</figcaption></figure>')


def expand_youtube_markers(md: str) -> str:
    return YOUTUBE_MARKER.sub(lambda m: youtube_embed(m.group(1), m.group(2), m.group(3) or ""), md)


def video_meta(slug: str, vid: str) -> dict:
    p = VIDEOS_DIR / slug / f"{vid}.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"title": vid}


def expand_video_markers(md: str, slug: str, with_media: bool, media_files: list[str]) -> str:
    """Replace {{video:id}} lines with a <video> embed (when the media exists and
    with_media is set) or an instructor callout. media_files collects relative
    paths (media/<id>.mp4, media/<id>.vtt) that the page's resource must ship."""

    def repl(m: re.Match) -> str:
        vid = m.group(1)
        meta = video_meta(slug, vid)
        title = html.escape(meta.get("title", vid))
        mp4 = MEDIA_DIR / slug / f"{vid}.mp4"
        vtt = MEDIA_DIR / slug / f"{vid}.vtt"
        if with_media and mp4.exists():
            media_files.append(f"media/{vid}.mp4")
            track = ""
            if vtt.exists():
                media_files.append(f"media/{vid}.vtt")
                track = f'<track kind="captions" src="media/{vid}.vtt" srclang="en" label="English" default>'
            transcript = MEDIA_DIR / slug / f"{vid}-transcript.md"
            note = ""
            if transcript.exists():
                media_files.append(f"media/{vid}-transcript.md")
                note = f' <a href="media/{vid}-transcript.md" target="_blank" rel="noopener">Transcript</a>.'
            # Explicit pixel dimensions: Moodle's media filter reads width as an integer, so "100%" becomes 100px.
            return (f'<figure class="video"><video controls preload="metadata" width="900" height="506" src="media/{vid}.mp4">{track}'
                    f'Your browser cannot play this video. <a href="media/{vid}.mp4">Download it</a>.</video>'
                    f'<figcaption><strong>{title}.</strong> Draft narration generated from the instructor\'s script; captions included.{note}</figcaption></figure>')
        summary = html.escape(meta.get("summary", ""))
        return (f'<div class="callout"><strong>Video: {title}.</strong> {summary} '
                f'(Instructor: build with <code>make_videos.py</code> or record and embed your own.)</div>')

    return VIDEO_MARKER.sub(repl, md)

# ----------------------------------------------------------------------------
# Minimal Markdown -> HTML (headings, lists, quotes, tables, code, inline marks)
# ----------------------------------------------------------------------------


def _inline(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![*\w])\*([^*]+)\*(?![*\w])", r"<em>\1</em>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)",
                  r'<a href="\2" target="_blank" rel="noopener">\1</a>', text)
    return text


def md_to_html(md: str) -> str:
    lines = md.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    i = 0
    para: list[str] = []

    def flush_para():
        if para:
            out.append("<p>" + _inline(" ".join(s.strip() for s in para)) + "</p>")
            para.clear()

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_para()
            i += 1
            code: list[str] = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            out.append("<pre><code>" + html.escape("\n".join(code)) + "</code></pre>")
            i += 1
            continue

        if not stripped:
            flush_para()
            i += 1
            continue

        if stripped.startswith("<"):            # raw HTML passthrough
            flush_para()
            out.append(line)
            i += 1
            continue

        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            flush_para()
            level = len(m.group(1))
            out.append(f"<h{level}>{_inline(m.group(2))}</h{level}>")
            i += 1
            continue

        if re.match(r"^(-{3,}|\*{3,})$", stripped):
            flush_para()
            out.append("<hr>")
            i += 1
            continue

        if stripped.startswith(">"):
            flush_para()
            quote: list[str] = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip()[1:].strip())
                i += 1
            out.append("<blockquote>" + md_to_html("\n".join(quote)) + "</blockquote>")
            continue

        if stripped.startswith("|"):
            flush_para()
            rows: list[str] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(lines[i].strip())
                i += 1
            rows = [r for r in rows if not re.match(r"^\|\s*:?-{2,}", r)]
            tbl = ["<table>"]
            for n, r in enumerate(rows):
                cells = [c.strip() for c in r.strip("|").split("|")]
                tag = "th" if n == 0 else "td"
                tbl.append("<tr>" + "".join(f"<{tag}>{_inline(c)}</{tag}>" for c in cells) + "</tr>")
            tbl.append("</table>")
            out.append("".join(tbl))
            continue

        m_ul = re.match(r"^(\s*)[-*]\s+(.*)$", line)
        m_ol = re.match(r"^(\s*)\d+[.)]\s+(.*)$", line)
        if m_ul or m_ol:
            flush_para()
            tag = "ul" if m_ul else "ol"
            pat = r"^(\s*)[-*]\s+(.*)$" if m_ul else r"^(\s*)\d+[.)]\s+(.*)$"
            items: list[str] = []
            while i < len(lines):
                m = re.match(pat, lines[i])
                if m:
                    items.append(m.group(2))
                    i += 1
                elif lines[i].startswith("  ") and lines[i].strip() and items:
                    items[-1] += " " + lines[i].strip()      # continuation line
                    i += 1
                else:
                    break
            out.append(f"<{tag}>" + "".join(f"<li>{_inline(it)}</li>" for it in items) + f"</{tag}>")
            continue

        para.append(line)
        i += 1

    flush_para()
    return "\n".join(out)


# ----------------------------------------------------------------------------
# Shared page styling (embedded so pages render on their own inside any LMS)
# ----------------------------------------------------------------------------

PAGE_CSS = """
:root{--navy:#0f2d6b;--navy2:#1f4ba3;--gold:#c3902f;--text:#081225;--muted:#65759a;--border:rgba(15,45,107,.14);--soft:rgba(15,45,107,.06)}
body.cc-page{font-family:'Atkinson Hyperlegible',Segoe UI,Arial,sans-serif;color:var(--text);line-height:1.6;max-width:860px;margin:0 auto;padding:24px 20px;background:#fff}
.cc-page h1,.cc-page h2,.cc-page h3{font-family:'Crimson Pro',Georgia,serif;color:var(--navy);line-height:1.2}
.cc-page h1{font-size:2rem;margin:.2em 0 .4em;border-bottom:3px solid var(--gold);padding-bottom:.3em}
.cc-page h2{font-size:1.45rem;margin:1.6em 0 .5em}
.cc-page h3{font-size:1.15rem;margin:1.3em 0 .4em}
.cc-page .kicker{display:inline-block;font-size:.78rem;letter-spacing:.08em;text-transform:uppercase;color:var(--gold);font-weight:700;margin-bottom:.4em}
.cc-page .callout{border-left:4px solid var(--gold);background:var(--soft);padding:12px 16px;border-radius:0 8px 8px 0;margin:1.2em 0}
.cc-page table{border-collapse:collapse;width:100%;margin:1em 0;font-size:.95rem}
.cc-page th,.cc-page td{border:1px solid var(--border);padding:8px 10px;text-align:left;vertical-align:top}
.cc-page th{background:var(--soft);color:var(--navy)}
.cc-page blockquote{margin:1em 0;padding:.4em 1em;border-left:3px solid var(--navy2);color:#2d3a59;background:#f7f9fe}
.cc-page pre{background:#0d2441;color:#e8eefc;padding:12px 14px;border-radius:8px;overflow:auto;font-size:.9rem}
.cc-page code{font-family:Consolas,Menlo,monospace;font-size:.92em}
.cc-page a{color:var(--navy2)}
.cc-page .meta{color:var(--muted);font-size:.9rem;margin-bottom:1.4em}
.cc-page .badge{display:inline-block;background:var(--navy);color:#fff;border-radius:999px;padding:2px 10px;font-size:.75rem;margin-right:6px}
.cc-page figure.video{margin:1.2em 0}
.cc-page figure.video video{width:100%;max-width:900px;border-radius:10px;background:#000}
.cc-page figure.video figcaption{color:var(--muted);font-size:.9rem;margin-top:.4em}
.cc-page .yt-wrap{position:relative;max-width:900px;aspect-ratio:16/9;border-radius:10px;overflow:hidden;background:#000}
.cc-page .yt-wrap iframe{position:absolute;inset:0;width:100%;height:100%;border:0}
"""

FONT_LINK = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700'
             '&family=Crimson+Pro:wght@500;600;700&display=swap">')


def wrap_page(title: str, body_html: str, kicker: str = "", meta: str = "") -> str:
    kick = f'<div class="kicker">{html.escape(kicker)}</div>' if kicker else ""
    meta_html = f'<div class="meta">{meta}</div>' if meta else ""
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>{FONT_LINK}<style>{PAGE_CSS}</style></head>
<body class="cc-page">{kick}<h1>{html.escape(title)}</h1>{meta_html}{body_html}</body></html>"""


# ----------------------------------------------------------------------------
# QTI 1.2 (Common Cartridge assessment profile)
# ----------------------------------------------------------------------------


def _meta(fields: dict[str, str]) -> str:
    return "<qtimetadata>" + "".join(
        f"<qtimetadatafield><fieldlabel>{k}</fieldlabel><fieldentry>{html.escape(str(v))}</fieldentry></qtimetadatafield>"
        for k, v in fields.items()) + "</qtimetadata>"


def _mattext(text: str, kind: str = "text/html") -> str:
    return f'<material><mattext texttype="{kind}">{html.escape(text)}</mattext></material>'


def _item_feedback(ident: str, text: str) -> str:
    if not text:
        return ""
    return f'<itemfeedback ident="{ident}"><flow_mat>{_mattext(text)}</flow_mat></itemfeedback>'


def qti_item(q: dict, n: int) -> str:
    ident = f"q{n}_{uuid.uuid4().hex[:8]}"
    qtype = q["type"]
    title = html.escape(q.get("title") or f"Question {n}")
    text_html = md_to_html(q["text"])
    fb_ok = q.get("feedback_correct") or q.get("feedback") or ""
    fb_bad = q.get("feedback_incorrect") or q.get("feedback") or ""

    if qtype in ("multiple_choice", "true_false"):
        profile = "cc.multiple_choice.v0p1" if qtype == "multiple_choice" else "cc.true_false.v0p1"
        if qtype == "true_false":
            options = ["True", "False"]
            idents = ["true", "false"]
            correct = "true" if q["answer"] else "false"
        else:
            options = q["options"]
            idents = [f"{ident}_a{k}" for k in range(len(options))]
            correct = idents[q["answer"]]
        labels = "".join(
            f'<response_label ident="{idn}">{_mattext(opt, "text/plain")}</response_label>'
            for idn, opt in zip(idents, options))
        presentation = (f'<presentation>{_mattext(text_html)}'
                        f'<response_lid ident="response1" rcardinality="Single"><render_choice>{labels}</render_choice></response_lid>'
                        f'</presentation>')
        resp = (f'<resprocessing><outcomes><decvar maxvalue="100" minvalue="0" varname="SCORE" vartype="Decimal"/></outcomes>'
                f'<respcondition continue="No"><conditionvar><varequal respident="response1">{correct}</varequal></conditionvar>'
                f'<setvar action="Set" varname="SCORE">100</setvar>'
                + (f'<displayfeedback feedbacktype="Response" linkrefid="{ident}_fb_ok"/>' if fb_ok else "")
                + '</respcondition>'
                + (f'<respcondition continue="Yes"><conditionvar><other/></conditionvar>'
                   f'<displayfeedback feedbacktype="Response" linkrefid="{ident}_fb_bad"/></respcondition>' if fb_bad else "")
                + '</resprocessing>')
        feedback = _item_feedback(f"{ident}_fb_ok", fb_ok) + _item_feedback(f"{ident}_fb_bad", fb_bad)

    elif qtype == "multiple_response":
        profile = "cc.multiple_response.v0p1"
        options = q["options"]
        idents = [f"{ident}_a{k}" for k in range(len(options))]
        labels = "".join(
            f'<response_label ident="{idn}">{_mattext(opt, "text/plain")}</response_label>'
            for idn, opt in zip(idents, options))
        presentation = (f'<presentation>{_mattext(text_html)}'
                        f'<response_lid ident="response1" rcardinality="Multiple"><render_choice>{labels}</render_choice></response_lid>'
                        f'</presentation>')
        conds = "".join(
            (f'<varequal respident="response1">{idn}</varequal>' if k in q["answers"]
             else f'<not><varequal respident="response1">{idn}</varequal></not>')
            for k, idn in enumerate(idents))
        resp = (f'<resprocessing><outcomes><decvar maxvalue="100" minvalue="0" varname="SCORE" vartype="Decimal"/></outcomes>'
                f'<respcondition continue="No"><conditionvar><and>{conds}</and></conditionvar>'
                f'<setvar action="Set" varname="SCORE">100</setvar>'
                + (f'<displayfeedback feedbacktype="Response" linkrefid="{ident}_fb_ok"/>' if fb_ok else "")
                + '</respcondition></resprocessing>')
        feedback = _item_feedback(f"{ident}_fb_ok", fb_ok)

    elif qtype == "essay":
        profile = "cc.essay.v0p1"
        presentation = (f'<presentation>{_mattext(text_html)}'
                        f'<response_str ident="response1" rcardinality="Single"><render_fib><response_label ident="answer1" rshuffle="No"/></render_fib></response_str>'
                        f'</presentation>')
        resp = ('<resprocessing><outcomes><decvar maxvalue="100" minvalue="0" varname="SCORE" vartype="Decimal"/></outcomes>'
                '<respcondition continue="No"><conditionvar><other/></conditionvar></respcondition></resprocessing>')
        feedback = ""
    else:
        raise ValueError(f"Unknown question type: {qtype}")

    return (f'<item ident="{ident}" title="{title}"><itemmetadata>'
            + _meta({"cc_profile": profile, "cc_question_category": "Course questions",
                     "cc_weighting": str(q.get("points", 1))})
            + f'</itemmetadata>{presentation}{resp}{feedback}</item>')


def build_qti(quiz: dict, ident: str) -> str:
    items = "".join(qti_item(q, n + 1) for n, q in enumerate(quiz["questions"]))
    meta = _meta({
        "cc_profile": "cc.exam.v0p1",
        "qmd_assessmenttype": "Examination",
        "qmd_scoretype": "Percentage",
        "qmd_feedbackpermitted": "Yes",
        "qmd_hintspermitted": "Yes",
        "qmd_solutionspermitted": "Yes",
        "qmd_timelimit": str(quiz.get("time_limit", 0)),
        "cc_allow_late_submission_check": "No",
        "cc_maxattempts": str(quiz.get("max_attempts", "unlimited")),
    })
    description = ""
    if quiz.get("description"):
        description = f'<presentation_material><flow_mat>{_mattext(md_to_html(quiz["description"]))}</flow_mat></presentation_material>'
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<questestinterop xmlns="http://www.imsglobal.org/xsd/ims_qtiasiv1p2" '
            f'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            f'xsi:schemaLocation="http://www.imsglobal.org/xsd/ims_qtiasiv1p2 '
            f'http://www.imsglobal.org/profile/cc/ccv1p1/ccv1p1_qtiasiv1p2p1_v1p0.xsd">'
            f'<assessment ident="{ident}" title="{html.escape(quiz["title"])}">{meta}{description}'
            f'<section ident="root_section">{items}</section></assessment></questestinterop>')


# ----------------------------------------------------------------------------
# Course build
# ----------------------------------------------------------------------------


def load_course(slug: str) -> tuple[dict, Path]:
    cdir = COURSES_DIR / slug
    course = json.loads((cdir / "course.json").read_text(encoding="utf-8"))
    course["slug"] = slug
    return course, cdir


def build_course(slug: str, with_media: bool = False) -> None:
    course, cdir = load_course(slug)
    build_dir = DIST_DIR / "_build" / slug
    if build_dir.exists():
        shutil.rmtree(build_dir)
    for sub in ("wiki_content", "wiki_content/media", "quizzes", "discussions", "links"):
        (build_dir / sub).mkdir(parents=True)
    shipped_media: set[str] = set()

    resources: list[str] = []
    org_items: list[str] = []
    preview_modules: list[dict] = []
    seq = 0

    def next_id(prefix: str) -> str:
        nonlocal seq
        seq += 1
        return f"{prefix}_{seq:03d}"

    for module in course["modules"]:
        mod_id = next_id("module")
        child_xml: list[str] = []
        preview_items: list[dict] = []
        for item in module["items"]:
            itype = item["type"]
            title = item["title"]
            rid = next_id(itype)
            kicker = f"{course.get('code', '')} - {module['title']}".strip(" -")

            if itype in ("page", "assignment"):
                media_files: list[str] = []
                md_src = expand_youtube_markers(
                    expand_video_markers((cdir / item["file"]).read_text(encoding="utf-8"), slug, with_media, media_files))
                body = md_to_html(md_src)
                meta = ""
                if itype == "assignment":
                    pts = item.get("points")
                    meta = '<span class="badge">Assignment</span>' + (f"{pts} points" if pts else "")
                page_html = wrap_page(title, body, kicker, meta)
                fname = f"wiki_content/{rid}.html"
                (build_dir / fname).write_text(page_html, encoding="utf-8")
                extra = ""
                for mf in media_files:
                    src = MEDIA_DIR / slug / Path(mf).name
                    dst = build_dir / "wiki_content" / mf
                    if not dst.exists():
                        shutil.copy2(src, dst)
                    shipped_media.add(mf)
                    extra += f'<file href="wiki_content/{mf}"/>'
                resources.append(f'<resource identifier="{rid}" type="webcontent" href="{fname}"><file href="{fname}"/>{extra}</resource>')
                preview_items.append({"id": rid, "type": itype, "title": title, "html": body,
                                      "points": item.get("points")})

            elif itype == "discussion":
                body = md_to_html((cdir / item["file"]).read_text(encoding="utf-8"))
                fname = f"discussions/{rid}.xml"
                xml = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
                       f'<topic xmlns="http://www.imsglobal.org/xsd/imsccv1p1/imsdt_v1p1" '
                       f'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                       f'xsi:schemaLocation="http://www.imsglobal.org/xsd/imsccv1p1/imsdt_v1p1 '
                       f'http://www.imsglobal.org/profile/cc/ccv1p1/ccv1p1_imsdt_v1p1.xsd">'
                       f'<title>{html.escape(title)}</title><text texttype="text/html">{html.escape(body)}</text></topic>')
                (build_dir / fname).write_text(xml, encoding="utf-8")
                resources.append(f'<resource identifier="{rid}" type="imsdt_xmlv1p1"><file href="{fname}"/></resource>')
                preview_items.append({"id": rid, "type": itype, "title": title, "html": body})

            elif itype == "quiz":
                quiz = json.loads((cdir / item["file"]).read_text(encoding="utf-8"))
                quiz.setdefault("title", title)
                fname = f"quizzes/{rid}.xml"
                (build_dir / fname).write_text(build_qti(quiz, rid), encoding="utf-8")
                resources.append(f'<resource identifier="{rid}" type="imsqti_xmlv1p2/imscc_xmlv1p1/assessment" href="{fname}"><file href="{fname}"/></resource>')
                preview_items.append({"id": rid, "type": itype, "title": title, "quiz": quiz})

            elif itype == "link":
                fname = f"links/{rid}.xml"
                xml = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
                       f'<webLink xmlns="http://www.imsglobal.org/xsd/imsccv1p1/imswl_v1p1" '
                       f'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                       f'xsi:schemaLocation="http://www.imsglobal.org/xsd/imsccv1p1/imswl_v1p1 '
                       f'http://www.imsglobal.org/profile/cc/ccv1p1/ccv1p1_imswl_v1p1.xsd">'
                       f'<title>{html.escape(title)}</title><url href="{html.escape(item["url"])}" target="_blank"/></webLink>')
                (build_dir / fname).write_text(xml, encoding="utf-8")
                resources.append(f'<resource identifier="{rid}" type="imswl_xmlv1p1"><file href="{fname}"/></resource>')
                preview_items.append({"id": rid, "type": itype, "title": title, "url": item["url"],
                                      "note": item.get("note", "")})
            else:
                raise ValueError(f"Unknown item type {itype} in {slug}")

            child_xml.append(f'<item identifier="{rid}_item" identifierref="{rid}"><title>{html.escape(title)}</title></item>')

        org_items.append(f'<item identifier="{mod_id}"><title>{html.escape(module["title"])}</title>{"".join(child_xml)}</item>')
        preview_modules.append({"title": module["title"], "summary": module.get("summary", ""), "items": preview_items})

    manifest = f"""<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="{slug}_{uuid.uuid4().hex[:8]}"
  xmlns="http://www.imsglobal.org/xsd/imsccv1p1/imscp_v1p1"
  xmlns:lom="http://ltsc.ieee.org/xsd/imsccv1p1/LOM/resource"
  xmlns:lomimscc="http://ltsc.ieee.org/xsd/imsccv1p1/LOM/manifest"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.imsglobal.org/xsd/imsccv1p1/imscp_v1p1 http://www.imsglobal.org/profile/cc/ccv1p1/ccv1p1_imscp_v1p2_v1p0.xsd
  http://ltsc.ieee.org/xsd/imsccv1p1/LOM/resource http://www.imsglobal.org/profile/cc/ccv1p1/LOM/ccv1p1_lomresource_v1p0.xsd
  http://ltsc.ieee.org/xsd/imsccv1p1/LOM/manifest http://www.imsglobal.org/profile/cc/ccv1p1/LOM/ccv1p1_lommanifest_v1p0.xsd">
  <metadata>
    <schema>IMS Common Cartridge</schema>
    <schemaversion>1.1.0</schemaversion>
    <lomimscc:lom>
      <lomimscc:general>
        <lomimscc:title><lomimscc:string language="en">{html.escape(course["title"])}</lomimscc:string></lomimscc:title>
        <lomimscc:description><lomimscc:string language="en">{html.escape(course["description"])}</lomimscc:string></lomimscc:description>
      </lomimscc:general>
    </lomimscc:lom>
  </metadata>
  <organizations>
    <organization identifier="org_1" structure="rooted-hierarchy">
      <item identifier="root">{"".join(org_items)}</item>
    </organization>
  </organizations>
  <resources>{"".join(resources)}</resources>
</manifest>"""
    (build_dir / "imsmanifest.xml").write_text(manifest, encoding="utf-8")

    DIST_DIR.mkdir(exist_ok=True)
    out = DIST_DIR / (f"{slug}-with-media.imscc" if with_media else f"{slug}.imscc")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(build_dir.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(build_dir).as_posix())

    write_preview(course, preview_modules, shipped_media)
    n_items = sum(len(m["items"]) for m in preview_modules)
    n_videos = len([m for m in shipped_media if m.endswith(".mp4")])
    print(f"built {out.relative_to(ROOT)}  ({len(preview_modules)} modules, {n_items} items, "
          f"{n_videos} videos, {out.stat().st_size // 1024} KB)")


# ----------------------------------------------------------------------------
# Browser preview of the whole course (no LMS needed)
# ----------------------------------------------------------------------------

PREVIEW_CSS = PAGE_CSS + """
body.cc-preview{max-width:none;margin:0;padding:0;display:grid;grid-template-columns:300px minmax(0,1fr);grid-template-areas:"side main";min-height:100vh;background:#f5f8ff}
/* Explicit areas: elements injected by browser extensions (Grammarly etc.) must not shift the layout */
body.cc-preview>nav.side{grid-area:side}
body.cc-preview>main{grid-area:main}
body.cc-preview>:not(nav.side):not(main){grid-column:1/-1}
.side{background:#0f2d6b;color:#dfe7f6;padding:24px 18px;position:sticky;top:0;height:100vh;overflow:auto}
.side h1{color:#fff;font-size:1.25rem;border:0;margin:0 0 4px}
.side .code{color:#c3902f;font-weight:700;font-size:.8rem;letter-spacing:.08em}
.side h2{color:#c3902f;font-size:.8rem;text-transform:uppercase;letter-spacing:.08em;margin:22px 0 6px}
.side a{color:#dfe7f6;text-decoration:none;display:block;padding:4px 8px;border-radius:6px;font-size:.9rem}
.side a:hover{background:rgba(255,255,255,.1)}
.side .t{display:inline-block;width:18px;color:#c3902f;font-size:.75rem}
main{padding:32px 48px;max-width:900px}
.card{background:#fff;border:1px solid var(--border);border-radius:14px;padding:28px 32px;margin-bottom:28px;box-shadow:0 12px 30px rgba(15,45,107,.06)}
.card h1{font-size:1.7rem}
.modhead{margin:40px 0 12px;padding-bottom:6px;border-bottom:2px solid var(--gold)}
.modhead h1{border:0;margin:0;font-size:1.5rem}
.modhead p{color:var(--muted);margin:.3em 0 0}
.q{border:1px solid var(--border);border-radius:10px;padding:14px 16px;margin:12px 0}
.q .opts label{display:block;padding:4px 0}
.q .ans{display:none;margin-top:8px;color:#0f2d6b;background:var(--soft);padding:8px 10px;border-radius:6px;font-size:.92rem}
.q.show .ans{display:block}
button.reveal{background:var(--navy);color:#fff;border:0;border-radius:6px;padding:6px 12px;cursor:pointer;font-size:.85rem;margin-top:6px}
.link a{font-weight:700}
@media (max-width:820px){body.cc-preview{grid-template-columns:1fr;grid-template-areas:"side" "main"}.side{position:static;height:auto}main{padding:20px 16px}}
"""


def write_preview(course: dict, modules: list[dict], shipped_media: set[str] | None = None) -> None:
    pdir = DIST_DIR / "preview" / course["slug"]
    pdir.mkdir(parents=True, exist_ok=True)
    if shipped_media:
        (pdir / "media").mkdir(exist_ok=True)
        for mf in shipped_media:
            shutil.copy2(MEDIA_DIR / course["slug"] / Path(mf).name, pdir / mf)
    icons = {"page": "P", "assignment": "A", "discussion": "D", "quiz": "Q", "link": "L"}
    labels = {"page": "Page", "assignment": "Assignment", "discussion": "Discussion forum",
              "quiz": "Quiz", "link": "Web link"}
    side = ['<a href="../index.html" style="font-size:.8rem;opacity:.85;margin-bottom:10px">&larr; All courses</a>',
            f'<div class="code">{html.escape(course.get("code", ""))}</div><h1>{html.escape(course["title"])}</h1>',
            f'<div style="font-size:.85rem;opacity:.8">{html.escape(course.get("instructor", ""))}</div>']
    body: list[str] = [f'<div class="card"><div class="kicker">Course overview</div><h1>{html.escape(course["title"])}</h1>'
                       f'{md_to_html(course["description"])}'
                       f'<p><strong>Audience:</strong> {html.escape(course.get("audience", ""))}<br>'
                       f'<strong>Duration:</strong> {html.escape(course.get("duration", ""))}<br>'
                       f'<strong>Instructor:</strong> {html.escape(course.get("instructor", ""))}</p></div>']
    for mi, m in enumerate(modules, 1):
        side.append(f'<h2>{html.escape(m["title"])}</h2>')
        body.append(f'<div class="modhead" id="m{mi}"><h1>{html.escape(m["title"])}</h1>'
                    + (f'<p>{html.escape(m["summary"])}</p>' if m["summary"] else "") + '</div>')
        for it in m["items"]:
            side.append(f'<a href="#{it["id"]}"><span class="t">{icons[it["type"]]}</span>{html.escape(it["title"])}</a>')
            label = labels[it["type"]]
            if it["type"] == "quiz":
                qz = it["quiz"]
                parts = [f'<div class="card" id="{it["id"]}"><div class="kicker">{label}</div><h1>{html.escape(it["title"])}</h1>',
                         md_to_html(qz.get("description", ""))]
                for n, q in enumerate(qz["questions"], 1):
                    name = f'{it["id"]}_{n}'
                    parts.append(f'<div class="q"><strong>{n}.</strong> {md_to_html(q["text"])}')
                    if q["type"] == "true_false":
                        parts.append(f'<div class="opts"><label><input type="radio" name="{name}"> True</label>'
                                     f'<label><input type="radio" name="{name}"> False</label></div>')
                        ans = "True" if q["answer"] else "False"
                    elif q["type"] in ("multiple_choice", "multiple_response"):
                        kind = "radio" if q["type"] == "multiple_choice" else "checkbox"
                        parts.append('<div class="opts">' + "".join(
                            f'<label><input type="{kind}" name="{name}"> {html.escape(o)}</label>' for o in q["options"]) + '</div>')
                        idx = [q["answer"]] if q["type"] == "multiple_choice" else q["answers"]
                        ans = "; ".join(q["options"][k] for k in idx)
                    else:
                        parts.append('<div class="opts"><textarea rows="4" style="width:100%"></textarea></div>')
                        ans = "Open response (instructor-graded)"
                    fb = q.get("feedback") or q.get("feedback_correct") or ""
                    parts.append('<button class="reveal" onclick="this.parentNode.classList.toggle(\'show\')">Show answer</button>'
                                 f'<div class="ans"><strong>Answer:</strong> {html.escape(ans)}'
                                 + (f'<br>{html.escape(fb)}' if fb else "") + '</div></div>')
                parts.append("</div>")
                body.append("".join(parts))
            elif it["type"] == "link":
                body.append(f'<div class="card link" id="{it["id"]}"><div class="kicker">{label}</div><h1>{html.escape(it["title"])}</h1>'
                            f'<p><a href="{html.escape(it["url"])}" target="_blank" rel="noopener">{html.escape(it["url"])}</a></p>'
                            + (f'<p>{html.escape(it["note"])}</p>' if it["note"] else "") + '</div>')
            else:
                pts = f' - {it["points"]} points' if it.get("points") else ""
                body.append(f'<div class="card" id="{it["id"]}"><div class="kicker">{label}{pts}</div><h1>{html.escape(it["title"])}</h1>{it["html"]}</div>')

    page = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Preview: {html.escape(course["title"])}</title>{FONT_LINK}<style>{PREVIEW_CSS}</style></head>
<body class="cc-page cc-preview"><nav class="side">{"".join(side)}</nav><main>{"".join(body)}</main></body></html>"""
    (pdir / "index.html").write_text(page, encoding="utf-8")


def main(argv: list[str]) -> None:
    with_media = "--with-media" in argv
    argv = [a for a in argv if a != "--with-media"]
    slugs = argv or sorted(p.name for p in COURSES_DIR.iterdir() if (p / "course.json").exists())
    for slug in slugs:
        build_course(slug, with_media=with_media)
    shutil.rmtree(DIST_DIR / "_build", ignore_errors=True)


if __name__ == "__main__":
    main(sys.argv[1:])
