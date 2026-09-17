# Course Authoring Guide

How to write a new course, or edit an existing one, in the source format the build script understands.

## Folder layout

```
lms/courses/<slug>/
  course.json          course metadata and the module/item map
  pages/*.md           content pages and lesson pages (Markdown)
  assignments/*.md     assignment instructions with rubric (Markdown)
  discussions/*.md     forum prompts (Markdown)
  quizzes/*.json       quizzes and surveys (JSON)
```

The slug is a lowercase, hyphenated folder name; it becomes the file name of the package.

## course.json

```json
{
  "code": "GENAI 101",
  "title": "Course title as learners see it",
  "description": "One paragraph. Shown in the catalog and the preview.",
  "audience": "Who the course is for",
  "duration": "Total time and pacing",
  "instructor": "Name, institution",
  "modules": [
    {
      "title": "Module 1: ...",
      "summary": "One sentence shown under the module heading in the preview.",
      "items": [
        {"type": "page",       "title": "...", "file": "pages/m1-intro.md"},
        {"type": "assignment", "title": "...", "file": "assignments/a1.md", "points": 50},
        {"type": "discussion", "title": "...", "file": "discussions/m1.md"},
        {"type": "quiz",       "title": "...", "file": "quizzes/m1.json"},
        {"type": "link",       "title": "...", "url": "https://...", "note": "Optional one-line note"}
      ]
    }
  ]
}
```

Item types and what they become after import:

| Type | Moodle | Canvas | Notes |
| --- | --- | --- | --- |
| page | File resource displaying the HTML page | Page | Full styling embedded; fonts load from Google Fonts |
| assignment | Same as page, with an "Assignment" badge and points | Page | Convert to a real Assignment activity after import (see setup guide) |
| discussion | Forum | Discussion | Prompt becomes the forum description |
| quiz | Quiz with question bank entries | Quiz | Question types below |
| link | URL resource | External URL | Opens in a new tab |

## Markdown subset

The build script has its own small Markdown converter. It supports:

- Headings: `#`, `##`, `###` (use `##` for the main sections of a page; the page title is added automatically as the H1).
- Paragraphs separated by blank lines.
- Bulleted lists (`-`) and numbered lists (`1.`). One level only; a continuation line indented two spaces joins the previous item.
- Bold `**text**`, italic `*text*`, inline code with backticks, links `[text](url)`.
- Tables in pipe format with a header row and a `| --- |` separator row.
- Block quotes starting with `>`.
- Fenced code blocks with three backticks.
- Horizontal rules `---`.
- Raw HTML: any line beginning with `<` is passed through unchanged. Use this for the callout box:

```html
<div class="callout"><strong>Lesson video (3 minutes).</strong> Embed here.</div>
```

Not supported: nested lists, images by Markdown syntax (use an `<img>` tag with alt text), footnotes.

## Videos

Put a marker on its own line where a video belongs:

```
{{video:m1-l1}}
```

The id names a script at `lms/videos/<slug>/<id>.json` and, once generated, a video at `lms/media/<slug>/<id>.mp4`. A normal build renders the marker as a callout with the video's title and summary. A `--with-media` build embeds the MP4 with its WebVTT captions and a transcript link, and ships the files inside the package.

Video script format:

```json
{
  "title": "Lesson 1.1: Composing an Original Song with GenAI",
  "subtitle": "GENAI 101 - Module 1: Music",
  "summary": "One sentence shown in the callout when media is not embedded.",
  "voice": "Microsoft Zira Desktop",
  "slides": [
    {"heading": "Slide heading", "bullets": ["Up to about six short bullets"], "narration": "What the narrator says for this slide. Two to five sentences."}
  ]
}
```

**YouTube videos** (for example the instructor's own recordings) use a second marker, also on its own line:

```
{{youtube:lnE1iTkWluk | Introduction: Music Lesson One}}
{{youtube:ZwEb9ss9b9A | The Symphony of Digital Skills | Optional caption text shown under the player.}}
```

The builder renders a responsive, privacy-enhanced embed (youtube-nocookie) with the title as the accessible name. Without a caption, the figure says the video was recorded by the instructor for the 2025 pilot. GENAI 101 embeds nine such videos from davidawoyemi.net/portfolio.html.

Generate draft videos with `python lms/scripts/make_videos.py <slug> <id>` (one video) or with no arguments (all). Each run also writes `<id>.vtt` and `<id>-transcript.md`. Keep narration conversational and under about 120 words per slide; the synthesizer reads numbers and abbreviations literally, so spell out "one hundred eighteen beats per minute" rather than "118 BPM" in narration text.

## Quiz JSON

```json
{
  "title": "Lesson 1.1 Knowledge Check",
  "description": "Shown at the top of the quiz. Markdown allowed.",
  "max_attempts": "unlimited",
  "time_limit": 0,
  "questions": [
    {
      "type": "multiple_choice",
      "text": "Question stem. **Markdown** allowed.",
      "options": ["A", "B", "C", "D"],
      "answer": 2,
      "feedback": "Shown after answering. Explain why the right answer is right.",
      "points": 1
    },
    {"type": "true_false", "text": "...", "answer": true, "feedback": "..."},
    {"type": "multiple_response", "text": "Select all that apply.", "options": ["A", "B", "C"], "answers": [0, 2], "feedback": "..."},
    {"type": "essay", "text": "Open response, instructor-graded or ungraded.", "points": 0}
  ]
}
```

- `answer` and `answers` are zero-based indexes into `options`.
- `feedback_correct` and `feedback_incorrect` can replace `feedback` for multiple choice and true/false.
- `max_attempts`: a number, or `"unlimited"`.
- For ungraded surveys set `"max_attempts": 1` and `"points": 0` on every question; the `answer` field is still required by the format, so pick any option.

## Writing standards

Follow the course template standard in `01-lms-design.md` section 7. In particular:

- Every lesson page opens with estimated time and the competencies or objectives it targets, then a video callout, then numbered learning objectives.
- Every lesson ends with "Create and share" instructions, resources, and reflection prompts.
- Every assignment ends with an analytic rubric table (four levels with point ranges) whose total matches `points` in `course.json`.
- Every quiz question has feedback.
- Use plain, direct sentences. Define acronyms at first use. Prefer "you" for learners.
- Do not name real students or include identifying data in cases or examples.

## Build and preview

```bash
python lms/scripts/build_cartridge.py                 # all courses
python lms/scripts/build_cartridge.py <slug>          # one course
```

Outputs:

- `lms/dist/<slug>.imscc`: the package to import.
- `lms/dist/preview/<slug>/index.html`: open in a browser to read the whole course, including quizzes with "Show answer" buttons.

The build fails loudly if a file referenced in `course.json` is missing, if a quiz has an unknown question type, or if JSON is malformed. Fix the source and rebuild.

## Editing a course that is already imported

Moodle does not merge a re-imported cartridge into an existing course. For small edits, change the content directly in Moodle **and** in the source files so they stay in sync. For large revisions, rebuild the package, restore it as a new course, move enrollments if needed, and retire the old one. Keep the source files as the canonical version.

## Adding a new course from existing materials

1. Copy an existing course folder and rename it.
2. Rewrite `course.json` with the new module map.
3. Draft Module 0 from the template (welcome, how it works, tools, responsible use, introduction forum, pre-assessment).
4. Write lesson pages following the seven-step pattern. Convert syllabus objectives into observable objectives first; everything else follows from them.
5. Write knowledge checks last, from the key ideas of each page; distractors should be the misconceptions you expect.
6. Build, preview, revise, import.
