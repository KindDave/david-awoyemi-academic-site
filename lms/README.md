# David Awoyemi Learning Studio (LMS)

A self-hosted Moodle learning management system plus an authoring pipeline that turns Markdown and JSON course sources into importable course packages.

## What is here

```
lms/
  docker/       docker-compose.yml, Caddyfile, .env.example   -> run Moodle
  docs/
    01-lms-design.md        platform decision, architecture, branding, course template standard, QA checklist
    02-moodle-setup.md      install, configure, brand, import courses, post-import checklist, backups
    03-course-authoring.md  source format, Markdown subset, quiz JSON, build and preview
  courses/
    art-integrated-genai-literacy/        GENAI 101 (4 modules, 8 lessons, 44 items)
    id-553-intro-instructional-design/    ID 553 (9 modules, 42 items, two original cases)
  videos/<slug>/*.json    narration scripts for the 24 course videos (slides + narration)
  media/<slug>/           generated videos (.mp4, git-ignored), captions (.vtt), transcripts (.md)
  scripts/
    build_cartridge.py    builds .imscc packages and browser previews (--with-media embeds videos)
    make_videos.py        renders slides, narrates with Windows text-to-speech, assembles MP4 + captions
    deploy_moodle.ps1     one-command deploy into the running Moodle container (brand, restore, configure)
    moodle_restore_cc.php restores a Common Cartridge from the CLI (Moodle's own CLI cannot)
    moodle_admin.php      branding, categories, assignment conversion, quiz/forum settings, test student
  dist/
    <slug>.imscc                import into Moodle, Canvas, or Blackboard (pages carry video callouts)
    <slug>-with-media.imscc     same, with all videos embedded (git-ignored; rebuild locally)
    preview/<slug>/index.html   read the whole course in a browser
```

**Rebuild everything from a fresh clone:**

```bash
winget install -e --id Gyan.FFmpeg --scope user    # once
python lms/scripts/make_videos.py                     # about 3 minutes for all 24 videos
python lms/scripts/build_cartridge.py --with-media
```

## Quick start

**Review the courses now, no server needed:** open `lms/dist/preview/art-integrated-genai-literacy/index.html` or `lms/dist/preview/id-553-intro-instructional-design/index.html` in a browser.

**Rebuild after editing content:**

```bash
python lms/scripts/build_cartridge.py
```

**Run Moodle locally:**

```bash
cd lms/docker
cp .env.example .env     # edit passwords
docker compose up -d     # open http://localhost after a few minutes
```

Then deploy the courses in one command (brands the site, restores both packages with videos, converts assignments, enrols a test student):

```bash
powershell -File lms/scripts/deploy_moodle.ps1
```

Details and the manual equivalent are in `docs/02-moodle-setup.md`.

## Courses

| Code | Title | Audience | Status |
| --- | --- | --- | --- |
| GENAI 101 | Art-Integrated GenAI Literacy for Music and Theater Educators | Pre-service and in-service arts teachers | Full draft; videos to record |
| ID 553 | Introduction to the Principles of Instructional Design | Graduate students and practitioners | Full draft; videos to record |

Both courses are complete drafts: every page, lesson, assignment, rubric, forum prompt, quiz, and video is in place. The videos are narrated slide videos generated from written scripts with a synthetic voice; each has captions and a transcript, and any of them can be re-recorded from its transcript. After import, the remaining manual step is converting assignment pages into Moodle Assignment activities (about 10 minutes per course; see the setup guide).
