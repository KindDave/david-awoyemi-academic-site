# Brief for the application assistant: LMS, accessibility, automation, and agentic AI

Purpose: give whoever prepares David Awoyemi's job materials (CV, resume, cover letters, teaching statements, portfolio pages) everything needed to add his learning-platform, accessibility, automation, and agentic-AI expertise. Every fact below is verifiable in the repository `KindDave/david-awoyemi-academic-site` (folder `lms/`) or on the live site. Written 2026-09-17.

## 1. How David's materials are produced (read first)

- `David_CV.docx` in the job-materials folder is the single source of truth. A build script parses it and regenerates the public website, so **add new content to the CV document, not to the website**. The one-click "Publish CV to website" launcher pushes it live.
- The parser recognises these all-caps section headings: PROFILE SUMMARY, EDUCATION, RESEARCH EXPERIENCE, TEACHING EXPERIENCE, INSTRUCTIONAL DESIGN EXPERIENCE, PUBLICATIONS, CONFERENCE PRESENTATIONS, GRANTS, AWARDS & SCHOLARSHIPS, CERTIFICATIONS, TECHNICAL AND PROFESSIONAL SKILLS, LEADERSHIP ROLE AND SERVICES, PROFESSIONAL AND COMMUNITY SERVICE, PROFESSIONAL AFFLIATIONS (sic), PROFESSIONAL REFERENCES INFORMATION. Keep those exact headings.
- Experience entries use this layout: a title line with a TAB and the date (`Title<TAB>Month Year`), then one organization line with no terminal period, then detail sentences (each ending in a period). Under TEACHING EXPERIENCE, entries may be grouped by the sub-headings "Courses Taught and Co-Designed", "Guest Lectures and Workshops", "Prior Teaching".
- The skills section currently has four categories: Research methods; Learning analytics; Immersive and AI systems; Instructional design. New categories may be added in the same "Category: item, item, item" format.
- Style: plain, specific, no em dashes, APA 7 for citations, first person only in statements and letters.

## 2. Facts about the project (as of 2026-09-17)

**The platform ("David Awoyemi Learning Studio")**

- A self-hosted learning management system on Moodle 4.5 LTS, deployed with Docker Compose (Moodle, MariaDB, Caddy reverse proxy with automatic HTTPS). Running and verified locally; production configuration prepared for a `learn.davidawoyemi.net` deployment.
- Site branded to match his academic website (theme colours, logo, Crimson Pro and Atkinson Hyperlegible typography), four course categories, self-enrolment with keys, test-student account.
- An authoring pipeline he owns: courses are written as structured source files (Markdown pages, JSON quizzes, a JSON course map) and compiled by a Python builder into **IMS Common Cartridge 1.1** packages with **QTI 1.2** assessments, which import into Moodle, Canvas, and Blackboard. The builder also produces a browser preview of every course.
- A scripted deployment (PowerShell plus two PHP admin scripts run inside the Moodle container) that brands the site, creates categories, restores the cartridges from the command line (Moodle's own CLI cannot restore cartridges; he ships a working replacement), converts assignment pages into graded Assignment activities with the right points, sets quiz and forum options, and enrols a test student. Re-runnable from a fresh clone.
- A video pipeline: narration scripts are rendered into branded slide videos with WebVTT captions and Markdown transcripts (24 videos, about 107 minutes total), embedded in the courses.
- Public showcase at **https://www.davidawoyemi.net/learn/** (catalog, full course previews with videos and quizzes, downloadable course packages) and a "Learning Studio" section on **https://www.davidawoyemi.net/portfolio.html**. Published through the site's GitHub Actions deployment.

**The courses (both complete, imported and verified in Moodle)**

| Course | Content | Assessment |
| --- | --- | --- |
| GENAI 101: Art-Integrated GenAI Literacy for Music and Theater Educators | 4 modules, 8 hands-on lessons (Suno, Soundtrap, Animaker, invideo AI, text models), 44 activities, 12 lesson videos plus 9 pilot-program videos | Competency-based: 7 GenAI competencies, gallery forums with 75-word rationales, 8 knowledge checks with feedback on every option, 2 rubric-graded reflections, final lesson-plan project with peer review, matched pre/post self-assessments |
| ID 553: Introduction to the Principles of Instructional Design | 9 modules, 42 activities, two original case studies (a hospital EHR rollout; a community-college AI-literacy initiative), 12 lecture videos; covers ID models, learner/context/task analysis, objectives and aligned assessment, strategies, multimedia and accessibility, prototyping, evaluation | 800-point graduate course: 9 assignments with analytic four-level rubrics, 5 knowledge checks, objective clinic and peer-review discussions |

GENAI 101 grows out of the Arts-Integrated GenAI Literacy Development Program he co-designed and delivered on UA Blackboard in 2025 (pre-service music and theater teachers). ID 553 builds on the AIL 602 Electronic Instructional Design studio he supported as mentored graduate teaching assistant and the ID 553 course he built in Canvas.

**Accessibility (built into the standard, not retrofitted)**

- Content standard: WCAG 2.2 AA. Every video has captions and a transcript link; real heading structure; 4.5:1 contrast; keyboard-operable interactions; Atkinson Hyperlegible body type (designed by the Braille Institute for legibility).
- Course template requires a low-tech alternative path for every activity, a UDL checkpoint selection in every instructional plan, and accessibility notes on every storyboard row.
- Responsive, privacy-enhanced video embeds (youtube-nocookie) with accessible names; layout hardened against browser-extension DOM injection.
- ID 553 teaches Mayer's multimedia principles, UDL, and WCAG explicitly (Module 6), with an accessibility checklist students apply to their own prototypes.

**Automation (verifiable in the same repository)**

- CV-to-website generator: parses `David_CV.docx` and regenerates a seven-page academic site plus JSON data; one-click publish script with dry-run and diff of changed sections; GitHub Actions builds and deploys on push.
- LMS pipeline as above: source to cartridge, cartridge to Moodle, scripts to video, all command-line and re-runnable; secrets and generated media kept out of version control by policy.
- Windows environment automation: winget-based installs, Docker Desktop and WSL bring-up, PowerShell orchestration.

**Agentic AI**

- He directs agentic coding assistants (Claude Code) to build and operate real systems: specifying goals and constraints, deciding architecture (self-hosted Moodle over a static hub or a custom app; Common Cartridge for portability), reviewing outputs, and verifying results in the running system.
- He designs human-in-the-loop AI production workflows, including a script-to-video pipeline that produces captioned, transcribed lesson videos in minutes, and responsible-AI disclosure practices applied across the platform.
- Curriculum: GENAI 101 teaches prompt engineering, AI feedback evaluation, AI ethics literacy (consent, likeness, ownership, disclosure), and computational thinking through creative production; CIE 499 AI Fluency for the Workforce (co-designed and taught, summer 2026) included a chatbot development project and AI toolkit assessments.
- Existing CV skills already list embodied AI feedback agents, generative AI and LLMs for instruction, prompt engineering, and adaptive learning systems design; the new material extends these into platform building and workflow automation.

## 3. Ready-to-use CV content

**INSTRUCTIONAL DESIGN EXPERIENCE (new entry, place first)**

```
Designer and Developer, David Awoyemi Learning Studio (self-hosted LMS)	Sept. 2026-present
Independent project; Moodle 4.5, Docker, IMS Common Cartridge, GitHub Actions
Designed and deployed a self-hosted learning management system with a course-authoring pipeline that compiles structured source files into IMS Common Cartridge packages importable into Moodle, Canvas, and Blackboard, and a scripted deployment that restores, configures, and enrols courses from the command line.
Built two complete online courses (86 activities, 21 rubrics and quizzes, 24 captioned videos) to a WCAG 2.2 AA and UDL content standard, including GENAI 101, developed from the arts-integrated GenAI literacy program delivered to pre-service teachers in 2025, and ID 553, a graduate introduction to instructional design with two original case studies.
Engineered an AI-assisted media pipeline with agentic coding tools that renders narration scripts into captioned, transcribed lesson videos, and applied responsible-AI disclosure practices across the platform.
Published the courses as a public showcase on the personal academic site (davidawoyemi.net/learn) through an automated build and deployment pipeline.
```

**TECHNICAL AND PROFESSIONAL SKILLS (two new categories)**

```
Learning platforms and standards: Moodle administration and theming, Blackboard Learn, Canvas, IMS Common Cartridge and QTI authoring, SCORM and xAPI packaging, Docker-based LMS deployment, WCAG 2.2 AA and UDL implementation, captioning and transcripts
Automation and agentic AI: Python build pipelines, GitHub Actions CI/CD, Docker Compose, PowerShell scripting, document-to-web generation, AI-assisted media production, directing agentic coding assistants (Claude Code), prompt engineering, responsible-AI disclosure practices
```

**PROFILE SUMMARY (one sentence to add)**

"I also build the platforms I teach on: a self-hosted, standards-based LMS and automated publishing pipelines, developed with automation and agentic AI tooling to WCAG 2.2 AA accessibility standards."

**Resume version (industry, learning experience designer or learning engineer roles)**

- Built and deployed a self-hosted Moodle LMS with a source-to-cartridge authoring pipeline; courses import into Moodle, Canvas, and Blackboard without rework.
- Shipped two complete courses (86 activities) to WCAG 2.2 AA with captions, transcripts, keyboard operability, and UDL-based alternatives.
- Automated deployment end to end (branding, restore, assignment conversion, quiz and forum configuration, enrolment) with re-runnable scripts; cut a multi-hour manual setup to one command.
- Built a script-to-video pipeline with agentic AI tooling that produces captioned, transcribed lesson videos in minutes (24 videos across two courses).
- Automated CV-to-website publishing with a one-click pipeline and CI/CD.

## 4. Cover letter paragraphs (adapt, do not paste verbatim)

**Faculty roles in instructional technology or learning design**

"Beyond studying learning technologies, I build them. This year I designed and deployed my own standards-based learning management system and published two complete courses on it: a graduate introduction to instructional design and an arts-integrated generative AI literacy course grown from a program I piloted with pre-service teachers. Both were built to WCAG 2.2 AA and Universal Design for Learning standards from the first draft, and both are open for review at davidawoyemi.net/learn. Building the platform, the authoring pipeline, and the deployment automation myself, using automation and agentic AI tooling, gives me a practitioner's understanding of the systems my students will design for."

**Instructional designer, learning engineer, or ed-tech roles**

"I work across the whole stack of learning design: needs analysis and objectives, rubric-aligned assessment, accessible multimedia, and the platform engineering that delivers it. Most recently I built a self-hosted LMS with an authoring pipeline that compiles course sources into IMS Common Cartridge packages, automated the deployment, and shipped two complete courses to WCAG 2.2 AA. I use agentic AI tools to accelerate production while keeping a human in the loop for every decision that reaches a learner."

**AI-focused roles (AI literacy, AI in education, responsible AI)**

"My AI work is practical and accountable. I teach generative AI literacy through creative production, I have co-designed and taught an undergraduate AI fluency course with a chatbot development project, and I build AI-assisted production workflows for my own courses, from script-to-video generation to disclosure practices. I direct agentic coding assistants to build and operate real systems, which is the literacy I want my students to have."

## 5. Interview talking points

- Why self-hosted Moodle rather than a static site or a custom app: gradebook, forums, research-ready surveys, and portability through Common Cartridge; the trade-off is server maintenance, mitigated by Docker and scripted deployment.
- What Moodle could not do out of the box and how he solved it: the CLI cannot restore cartridges (he wrote a replacement following the web restore sequence); cartridges import HTML as Page activities and assignments have no cartridge type (his post-import script converts them with rubrics and points); the media filter misreads percentage widths (fixed in the builder).
- Accessibility as a build standard: captions and transcripts generated with the media, hyperlegible type, contrast, keyboard operability, low-tech alternatives, and layout hardened against extension injection after a real user report.
- Agentic AI as a collaborator: he sets goals and constraints, the assistant executes, he verifies in the running system.
- Research angle: the pilot program these courses grow from was an IRB-approved study with pre/post surveys, usability and engagement measures, and participant artifacts; the new platform keeps that instrumentation.

## 6. Keywords for applicant tracking systems

Moodle, Learning Management System, LMS administration, IMS Common Cartridge, QTI, SCORM, xAPI, LTI, Canvas, Blackboard Learn, Docker, Docker Compose, GitHub Actions, CI/CD, Python, PowerShell, PHP, WCAG 2.2, Section 508, Universal Design for Learning, captioning, transcripts, accessible multimedia, instructional design, ADDIE, SAM, Dick and Carey, backward design, Merrill's First Principles, Mayer's multimedia principles, rubric design, competency-based assessment, learning analytics, generative AI, prompt engineering, AI literacy, responsible AI, human-in-the-loop, agentic AI, Claude Code, automation, content pipelines, course authoring.

## 7. Links to include

- Showcase: https://www.davidawoyemi.net/learn/
- Portfolio section: https://www.davidawoyemi.net/portfolio.html#learning-studio
- Source code and documentation: https://github.com/KindDave/david-awoyemi-academic-site/tree/main/lms
- Design specification: `lms/docs/01-lms-design.md` in that repository (platform decision, architecture, course template standard, quality checklist)

## 8. Keep these numbers current

Modules, activities, assignments, quizzes, and video counts are computed from the course sources at every site build and shown on the showcase page. Before reusing a number in a document, check the live page. When Moodle is hosted publicly, add the live address alongside the showcase link.
