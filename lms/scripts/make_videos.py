#!/usr/bin/env python3
"""Generate narrated slide videos (MP4 + WebVTT captions + transcript) from video scripts.

Usage:
    python lms/scripts/make_videos.py                     # all scripts in lms/videos/<slug>/*.json
    python lms/scripts/make_videos.py <slug>              # one course
    python lms/scripts/make_videos.py <slug> <video-id>   # one video

Each script is a JSON file:
    {
      "title": "Lesson 1.1: Composing an Original Song with GenAI",
      "subtitle": "GENAI 101 - Module 1: Music",
      "voice": "Microsoft Zira Desktop",      (optional; any installed Windows voice)
      "slides": [
        {"heading": "...", "bullets": ["...", "..."], "narration": "What the narrator says."},
        ...
      ]
    }

Output (per video) in lms/media/<slug>/:
    <id>.mp4            1280x720 H.264 video with AAC narration
    <id>.vtt            WebVTT captions, one cue per sentence
    <id>-transcript.md  Full narration script for accessibility and for re-recording

Narration uses the Windows speech synthesizer (System.Speech) so it runs offline. The
result is a draft narration; the instructor can re-record any video from the transcript.
Requires ffmpeg (installed via winget: Gyan.FFmpeg) and Pillow.
"""
from __future__ import annotations

import glob
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "videos"
MEDIA_DIR = ROOT / "media"
WORK_DIR = Path(os.environ.get("LMS_VIDEO_WORK", ROOT / "dist" / "_video_work"))

W, H = 1280, 720
NAVY, NAVY2, GOLD, TEXT, MUTED, BG = "#0f2d6b", "#1f4ba3", "#c3902f", "#081225", "#65759a", "#f5f8ff"
FONT_DIR = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
DEFAULT_VOICE = "Microsoft Zira Desktop"


def ffmpeg_path() -> str:
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    hits = glob.glob(os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*\**\bin\ffmpeg.exe"), recursive=True)
    if hits:
        return hits[0]
    raise SystemExit("ffmpeg not found. Install with: winget install -e --id Gyan.FFmpeg --scope user")


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    candidates = {"serif": ["georgiab.ttf", "georgia.ttf"], "serif-regular": ["georgia.ttf"],
                  "sans": ["segoeui.ttf", "arial.ttf"], "sans-bold": ["segoeuib.ttf", "arialbd.ttf"]}
    for f in candidates[name]:
        p = FONT_DIR / f
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


# ----------------------------------------------------------------------------
# Slide rendering
# ----------------------------------------------------------------------------

def wrap_text(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=fnt) <= max_width:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def render_title_slide(path: Path, title: str, subtitle: str, instructor: str) -> None:
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    d.rectangle([0, H - 90, W, H], fill=GOLD)
    d.rectangle([80, 150, 92, 470], fill=GOLD)
    y = 160
    for line in wrap_text(d, title, font("serif", 60), W - 220):
        d.text((120, y), line, font=font("serif", 60), fill="white")
        y += 74
    d.text((120, y + 16), subtitle, font=font("sans", 32), fill="#dfe7f6")
    d.text((120, y + 70), instructor, font=font("sans", 26), fill="#c3902f")
    d.text((120, H - 62), "Draft narration generated from the instructor's script", font=font("sans", 22), fill=NAVY)
    img.save(path)


def render_content_slide(path: Path, heading: str, bullets: list[str], footer: str, n: int, total: int) -> None:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 14], fill=NAVY)
    d.rectangle([0, 14, W, 20], fill=GOLD)
    y = 58
    hf = font("serif", 46)
    for line in wrap_text(d, heading, hf, W - 160):
        d.text((80, y), line, font=hf, fill=NAVY)
        y += 56
    d.line([80, y + 10, 400, y + 10], fill=GOLD, width=4)
    y += 40
    bf = font("sans", 30)
    max_lines = 11
    used = 0
    for b in bullets:
        lines = wrap_text(d, b, bf, W - 220)
        if used + len(lines) > max_lines:
            break
        d.ellipse([84, y + 14, 98, y + 28], fill=GOLD)
        for k, line in enumerate(lines):
            d.text((120, y), line, font=bf, fill=TEXT)
            y += 42
        y += 12
        used += len(lines)
    d.rectangle([0, H - 54, W, H], fill="white")
    d.line([0, H - 54, W, H - 54], fill="#dfe7f6", width=2)
    d.text((80, H - 40), footer, font=font("sans", 20), fill=MUTED)
    d.text((W - 160, H - 40), f"{n} / {total}", font=font("sans", 20), fill=MUTED)
    img.save(path)


# ----------------------------------------------------------------------------
# Narration (Windows System.Speech, offline)
# ----------------------------------------------------------------------------

def synthesize(items: list[tuple[str, Path]], voice: str) -> None:
    """items: (text, wav_path). One PowerShell process for the whole video."""
    spec = json.dumps([{"text": t, "path": str(p)} for t, p in items])
    spec_path = WORK_DIR / "tts_spec.json"
    spec_path.write_text(spec, encoding="utf-8")
    ps = f"""
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {{ $s.SelectVoice('{voice}') }} catch {{ }}
$s.Rate = -1
$items = Get-Content -Raw -Encoding UTF8 '{spec_path}' | ConvertFrom-Json
foreach ($i in $items) {{
  $s.SetOutputToWaveFile($i.path, (New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(22050, [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen, [System.Speech.AudioFormat.AudioChannel]::Mono)))
  $s.Speak($i.text)
  $s.SetOutputToNull()
}}
$s.Dispose()
"""
    ps_path = WORK_DIR / "tts.ps1"
    ps_path.write_text(ps, encoding="utf-8-sig")
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps_path)], check=True)


def wav_seconds(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / float(w.getframerate())


# ----------------------------------------------------------------------------
# Captions
# ----------------------------------------------------------------------------

def ts(sec: float) -> str:
    ms = int(round(sec * 1000))
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p]


def build_vtt(cues: list[tuple[float, float, str]]) -> str:
    out = ["WEBVTT", ""]
    for n, (a, b, t) in enumerate(cues, 1):
        out += [str(n), f"{ts(a)} --> {ts(b)}", "\n".join(textwrap.wrap(t, 60)), ""]
    return "\n".join(out)


# ----------------------------------------------------------------------------
# Build one video
# ----------------------------------------------------------------------------

def build_video(slug: str, script_path: Path) -> None:
    vid = script_path.stem
    spec = json.loads(script_path.read_text(encoding="utf-8"))
    out_dir = MEDIA_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    work = WORK_DIR / slug / vid
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    slides = spec["slides"]
    total = len(slides) + 1
    footer = spec.get("subtitle", "")
    instructor = spec.get("instructor", "Idowu David Awoyemi, The University of Alabama")

    # 1. slides
    pngs: list[Path] = []
    p = work / "slide_00.png"
    render_title_slide(p, spec["title"], footer, instructor)
    pngs.append(p)
    for n, s in enumerate(slides, 1):
        p = work / f"slide_{n:02d}.png"
        render_content_slide(p, s["heading"], s.get("bullets", []), footer, n + 1, total)
        pngs.append(p)

    # 2. narration
    intro = spec.get("intro_narration") or f"{spec['title']}. {footer}. Presented by {instructor}."
    narrations = [intro] + [s["narration"] for s in slides]
    wavs = [work / f"slide_{n:02d}.wav" for n in range(total)]
    synthesize(list(zip(narrations, wavs)), spec.get("voice", DEFAULT_VOICE))

    # 3. per-slide segments, then concat
    ff = ffmpeg_path()
    pad = 0.6  # seconds of silence after each slide's narration
    segs: list[Path] = []
    durations: list[float] = []
    for n, (png, wav) in enumerate(zip(pngs, wavs)):
        dur = wav_seconds(wav) + pad
        durations.append(dur)
        seg = work / f"seg_{n:02d}.ts"
        subprocess.run([ff, "-y", "-loglevel", "error",
                        "-loop", "1", "-framerate", "5", "-i", str(png),
                        "-i", str(wav),
                        "-filter_complex", f"[1:a]apad=pad_dur={pad}[a]",
                        "-map", "0:v", "-map", "[a]",
                        "-t", f"{dur:.3f}",
                        "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage", "-crf", "26",
                        "-pix_fmt", "yuv420p", "-r", "5",
                        "-c:a", "aac", "-b:a", "64k", "-ar", "22050", "-ac", "1",
                        "-f", "mpegts", str(seg)], check=True)
        segs.append(seg)
    concat = work / "concat.txt"
    concat.write_text("".join(f"file '{s.as_posix()}'\n" for s in segs), encoding="utf-8")
    mp4 = out_dir / f"{vid}.mp4"
    subprocess.run([ff, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(concat),
                    "-c", "copy", "-movflags", "+faststart", str(mp4)], check=True)

    # 4. captions: sentences within each slide, timed proportionally to length
    cues: list[tuple[float, float, str]] = []
    t = 0.0
    for text, dur in zip(narrations, durations):
        sents = sentences(text)
        speech = dur - pad
        total_chars = sum(len(s) for s in sents) or 1
        cursor = t
        for s in sents:
            length = speech * len(s) / total_chars
            cues.append((cursor, cursor + length, s))
            cursor += length
        t += dur
    (out_dir / f"{vid}.vtt").write_text(build_vtt(cues), encoding="utf-8")

    # 5. transcript
    lines = [f"# {spec['title']}", "", f"*{footer}*", "", f"Draft narration script. Total running time about {int(sum(durations) // 60)} min {int(sum(durations) % 60)} s.", ""]
    lines += ["## Title slide", "", intro, ""]
    for n, s in enumerate(slides, 1):
        lines += [f"## Slide {n + 1}: {s['heading']}", ""]
        for b in s.get("bullets", []):
            lines.append(f"- {b}")
        lines += ["", s["narration"], ""]
    (out_dir / f"{vid}-transcript.md").write_text("\n".join(lines), encoding="utf-8")

    size_kb = mp4.stat().st_size // 1024
    print(f"built {mp4.relative_to(ROOT)}  ({total} slides, {sum(durations):.0f}s, {size_kb} KB)")


def main(argv: list[str]) -> None:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    slugs = [argv[0]] if argv else sorted(p.name for p in SCRIPTS_DIR.iterdir() if p.is_dir())
    for slug in slugs:
        scripts = sorted((SCRIPTS_DIR / slug).glob("*.json"))
        if len(argv) > 1:
            scripts = [SCRIPTS_DIR / slug / f"{argv[1]}.json"]
        for sp in scripts:
            build_video(slug, sp)


if __name__ == "__main__":
    main(sys.argv[1:])
