from __future__ import annotations

import html
import json
import re
import shutil
from datetime import date
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parent.parent
SOURCE_DOCX = ROOT / "CV_David.docx"
OUTPUT_HTML = ROOT / "index.html"
OUTPUT_JSON = ROOT / "site-data.json"
STYLESHEET = ROOT / "styles.css"
DIST_DIR = ROOT / "dist"
DIST_HTML = DIST_DIR / "index.html"
DIST_JSON = DIST_DIR / "site-data.json"
DIST_STYLES = DIST_DIR / "styles.css"
DIST_DOCX = DIST_DIR / SOURCE_DOCX.name
NOJEKYLL = DIST_DIR / ".nojekyll"

DOCX_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
SECTION_TITLES = {
    "PROFILE SUMMARY",
    "EDUCATION",
    "RESEARCH EXPERIENCE",
    "TEACHING EXPERIENCE",
    "PUBLICATIONS",
    "CONFERENCE PRESENTATIONS",
    "GRANTS",
    "INSTRUCTIONAL DESIGN EXPERIENCE",
    "LEADERSHIP ROLE AND SERVICES",
    "PROFESSIONAL AND COMMUNITY SERVICE",
    "AWARDS & SCHOLARSHIPS",
    "CERTIFICATIONS",
    "TECHNICAL AND PROFESSIONAL SKILLS",
    "PROFESSIONAL AFFLIATIONS",
    "PROFESSIONAL REFERENCES INFORMATION",
}

DATE_PATTERNS = (
    r"^\d{4}\s*[-–]\s*(Present|\d{4})$",
    r"^\d{1,2}/\d{4}\s*[-–]\s*\d{1,2}/\d{4}$",
    r"^\d{1,2}/\d{1,2}/\d{4}$",
    r"^[A-Za-z]+\s+\d{4}$",
    r"^[A-Za-z]+\s+\d{1,2},\s*\d{4}$",
    r"^[A-Za-z]+\s+\d{1,2}[–-]\d{1,2},\s*\d{4}$",
    r"^[A-Za-z]+\s+\d{1,2}[–-]\d{1,2},\s*\d{4}\.$",
    r"^\d{4},\s*\d{4}$",
    r"^\d{4}$",
)

ORG_HINTS = (
    "University",
    "School",
    "College",
    "Office",
    "Lab",
    "Laboratory",
    "Program",
    "Campus",
    "Association",
    "Society",
    "Fellowship",
    "Technology",
    "Tuscaloosa",
    "Nigeria",
    "Minna",
    "Alabama",
)


def read_docx_paragraphs(path: Path) -> list[str]:
    with ZipFile(path) as docx_zip:
        xml = docx_zip.read("word/document.xml")
    root = ET.fromstring(xml)
    paragraphs: list[str] = []
    for paragraph in root.findall(".//w:p", DOCX_NS):
        text_runs = [node.text or "" for node in paragraph.findall(".//w:t", DOCX_NS)]
        text = normalize_whitespace("".join(text_runs))
        if text:
            paragraphs.append(text)
    return paragraphs


def normalize_whitespace(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = text.replace("\u200b", "")
    return re.sub(r"\s+", " ", text).strip()


def split_sections(paragraphs: list[str]) -> tuple[list[str], dict[str, list[str]]]:
    header: list[str] = []
    sections: dict[str, list[str]] = {}
    current: str | None = None

    for paragraph in paragraphs:
        if paragraph in SECTION_TITLES:
            current = paragraph
            sections[current] = []
            continue

        if current is None:
            header.append(paragraph)
        else:
            sections[current].append(paragraph)

    return header, sections


def is_date_line(text: str) -> bool:
    cleaned = text.strip().rstrip(".")
    return any(re.match(pattern, cleaned) for pattern in DATE_PATTERNS)


def extract_email(text: str) -> str:
    match = re.search(r"[\w.\-+]+@[\w.\-]+\.\w+", text)
    return match.group(0) if match else ""


def extract_phone(text: str) -> str:
    match = re.search(r"\(\d{3}\)\s*\d{3}-\d{4}", text)
    return match.group(0) if match else ""


def phone_href(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)
    return f"+{digits}" if digits else ""


def infer_location(header_lines: list[str]) -> str:
    for line in header_lines:
        if "Tuscaloosa" in line:
            return "Tuscaloosa, Alabama"
    return ""


def parse_education(lines: list[str]) -> list[dict[str, str]]:
    education: list[dict[str, str]] = []
    for index in range(0, len(lines), 3):
        chunk = lines[index:index + 3]
        if len(chunk) == 3:
            education.append(
                {
                    "degree": chunk[0],
                    "institution": chunk[1],
                    "date": chunk[2],
                }
            )
    return education


def is_subheading(text: str) -> bool:
    if text in SECTION_TITLES:
        return False
    if text.startswith("["):
        return False
    if is_date_line(text):
        return False
    return text.istitle() or text in {
        "Peer-reviewed Journal Articles",
        "Referred Conference Proceedings",
        "Book Chapters",
        "Journal Reviews",
        "Conference Chair and Discussant",
        "Conference Reviews",
        "Mentoring",
        "Community/Outreach/ Conferences Services",
    }


def group_subsections(lines: list[str]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    current = "default"
    grouped[current] = []

    for line in lines:
        if is_subheading(line):
            current = line
            grouped[current] = []
            continue
        grouped.setdefault(current, []).append(line)

    return grouped


def list_items(lines: list[str]) -> list[str]:
    items: list[str] = []
    buffer = ""
    for line in lines:
        normalized_line = re.sub(r"\s(?=(?:\[\d+\]|\d+\]))", "\n", line).splitlines()
        for part in normalized_line:
            chunk = part.strip()
            if not chunk:
                continue
            if re.match(r"^\d+\]", chunk):
                chunk = f"[{chunk}"
            if chunk.startswith("["):
                if buffer:
                    items.append(buffer.strip())
                buffer = chunk
            elif buffer:
                buffer = f"{buffer} {chunk}".strip()
            else:
                items.append(chunk)
    if buffer:
        items.append(buffer.strip())
    return items


def looks_like_title(text: str) -> bool:
    if text.startswith("[") or is_date_line(text):
        return False
    if len(text) > 120 or text.endswith(".") or "http" in text.lower():
        return False
    if text == text.upper():
        return False
    return True


def looks_like_org(text: str) -> bool:
    return any(hint in text for hint in ORG_HINTS) or "," in text


def parse_entries(lines: list[str]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    index = 0

    while index < len(lines):
        current = lines[index]
        next_line = lines[index + 1] if index + 1 < len(lines) else ""

        if not (looks_like_title(current) and next_line):
            index += 1
            continue

        title = current
        organization = ""
        date_text = ""
        details: list[str] = []
        index += 1

        if index < len(lines) and looks_like_org(lines[index]) and not is_date_line(lines[index]):
            organization = lines[index]
            index += 1

        while index < len(lines):
            value = lines[index]
            upcoming = lines[index + 1] if index + 1 < len(lines) else ""

            if is_date_line(value):
                date_text = value.rstrip(".")
                index += 1
                continue

            if looks_like_title(value) and upcoming and not looks_like_org(upcoming):
                break

            if looks_like_title(value) and upcoming and looks_like_org(upcoming):
                break

            details.append(value)
            index += 1

        entries.append(
            {
                "title": title,
                "organization": organization,
                "date": date_text,
                "details": details,
            }
        )

    return entries


def pick_sentence(lines: list[str], fallback: str = "") -> str:
    text = " ".join(line for line in lines if not is_date_line(line)).strip()
    if not text:
        return fallback
    if len(text) <= 280:
        return text
    shortened = text[:277].rsplit(" ", 1)[0]
    return f"{shortened}..."


def clean_item_prefix(text: str) -> str:
    return re.sub(r"^\[\d+\]\s*", "", text).strip()


def first_matching_line(lines: list[str], needles: tuple[str, ...], fallback: str) -> str:
    lowered_needles = tuple(needle.lower() for needle in needles)
    for line in lines:
        lowered = line.lower()
        if any(needle in lowered for needle in lowered_needles):
            return line
    return fallback


def parse_skills(lines: list[str]) -> list[dict[str, str]]:
    skills: list[dict[str, str]] = []
    index = 0
    while index < len(lines):
        category = lines[index]
        details = lines[index + 1] if index + 1 < len(lines) else ""
        skills.append({"category": category, "details": details})
        index += 2
    return skills


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def to_feature_cards(items: list[str], limit: int) -> list[str]:
    return [clean_item_prefix(item) for item in items[:limit]]


def build_site_data() -> dict[str, Any]:
    paragraphs = read_docx_paragraphs(SOURCE_DOCX)
    header, sections = split_sections(paragraphs)

    publications_grouped = group_subsections(sections.get("PUBLICATIONS", []))
    conference_items = list_items(sections.get("CONFERENCE PRESENTATIONS", []))
    grants_lines = sections.get("GRANTS", [])
    awards_lines = sections.get("AWARDS & SCHOLARSHIPS", [])
    skills = parse_skills(sections.get("TECHNICAL AND PROFESSIONAL SKILLS", []))

    research_entries = parse_entries(sections.get("RESEARCH EXPERIENCE", []))
    teaching_entries = parse_entries(sections.get("TEACHING EXPERIENCE", []))
    design_entries = parse_entries(sections.get("INSTRUCTIONAL DESIGN EXPERIENCE", []))
    leadership_entries = parse_entries(sections.get("LEADERSHIP ROLE AND SERVICES", []))

    all_experience_entries = research_entries + teaching_entries + design_entries
    featured_experience = []
    for entry in all_experience_entries[:5]:
        featured_experience.append(
            {
                "date": entry["date"] or "Selected role",
                "title": entry["title"],
                "organization": entry["organization"],
                "summary": pick_sentence(entry["details"]),
            }
        )

    leadership_cards = []
    for entry in leadership_entries[:4]:
        leadership_cards.append(
            {
                "title": entry["title"],
                "body": pick_sentence(entry["details"], entry["organization"]),
            }
        )

    journal_articles = list_items(publications_grouped.get("Peer-reviewed Journal Articles", []))

    header_text = " ".join(header)
    email = extract_email(header_text)
    phone = extract_phone(header_text)

    research_lines = sections.get("RESEARCH EXPERIENCE", [])
    profile_lines = sections.get("PROFILE SUMMARY", [])
    skill_lines = sections.get("TECHNICAL AND PROFESSIONAL SKILLS", [])
    publication_lines = journal_articles

    data = {
        "generated_on": date.today().isoformat(),
        "source_file": SOURCE_DOCX.name,
        "person": {
            "name": header[0] if header else "Idowu David Awoyemi",
            "affiliation": header[1] if len(header) > 1 else "",
            "location": infer_location(header),
            "phone": phone,
            "phone_href": phone_href(phone),
            "email": email,
            "expected_phd": "Spring 2027",
        },
        "profile_summary": profile_lines[0] if profile_lines else "",
        "education": parse_education(sections.get("EDUCATION", [])),
        "research_themes": [
            {
                "title": "Immersive Learning",
                "body": first_matching_line(
                    research_lines,
                    ("immersive virtual reality", "virtual reality", "ivr"),
                    "Designing immersive virtual reality learning experiences for engineering and STEM education.",
                ),
            },
            {
                "title": "Learning Analytics",
                "body": first_matching_line(
                    research_lines,
                    ("learner analytics", "statistical analysis", "qualitative and quantitative"),
                    "Using learning analytics and mixed methods to understand engagement, behavior, and outcomes.",
                ),
            },
            {
                "title": "AI in Education",
                "body": first_matching_line(
                    skill_lines,
                    ("generative ai", "adaptive learning", "ai-assisted", "applied ai"),
                    "Exploring AI-enhanced instructional design, assessment, and digital learning environments.",
                ),
            },
            {
                "title": "Equity and Participation",
                "body": first_matching_line(
                    publication_lines,
                    ("broadening participation", "teachers of color", "reduced inequality"),
                    "Building inclusive and equitable pathways into computing and STEM learning.",
                ),
            },
        ],
        "metrics": [
            {"value": str(len(journal_articles)), "label": "peer-reviewed journal articles listed"},
            {"value": str(len(conference_items)), "label": "conference presentations and accepted sessions"},
            {"value": str(len(grants_lines)), "label": "grants, fellowships, and funded initiatives"},
            {"value": "2023-2026", "label": "current span of research, teaching, and service momentum"},
        ],
        "featured_experience": featured_experience,
        "selected_publications": to_feature_cards(journal_articles, 6),
        "recent_presentations": to_feature_cards(conference_items, 6),
        "grants_and_recognition": grants_lines[:6],
        "skills": [skill["category"] for skill in skills],
        "skill_details": skills,
        "leadership_cards": leadership_cards,
        "service_highlights": sections.get("PROFESSIONAL AND COMMUNITY SERVICE", [])[:10],
        "awards": awards_lines[:8],
        "publications_breakdown": {
            key: list_items(value) for key, value in publications_grouped.items() if key != "default"
        },
        "raw_sections": sections,
    }
    return data


def render_html(data: dict[str, Any]) -> str:
    person = data["person"]
    education_html = "\n".join(
        f"""
              <article>
                <span>{escape(item['date'])}</span>
                <strong>{escape(item['degree'])}</strong>
                <p>{escape(item['institution'])}</p>
              </article>
        """.rstrip()
        for item in data["education"]
    )

    research_themes_html = "\n".join(
        f"""
          <article class="topic-card">
            <h3>{escape(item['title'])}</h3>
            <p>{escape(item['body'])}</p>
          </article>
        """.rstrip()
        for item in data["research_themes"]
    )

    experience_html = "\n".join(
        f"""
          <article class="timeline-item">
            <div class="timeline-date">{escape(item['date'])}</div>
            <div class="timeline-content">
              <h3>{escape(item['title'])}</h3>
              <p class="timeline-org">{escape(item['organization'])}</p>
              <p>{escape(item['summary'])}</p>
            </div>
          </article>
        """.rstrip()
        for item in data["featured_experience"]
    )

    metrics_html = "\n".join(
        f"""
        <article>
          <strong>{escape(item['value'])}</strong>
          <span>{escape(item['label'])}</span>
        </article>
        """.rstrip()
        for item in data["metrics"]
    )

    publications_html = render_list_items(data["selected_publications"])
    presentations_html = render_list_items(data["recent_presentations"])
    grants_html = render_list_items(data["grants_and_recognition"])
    skill_tags_html = "\n".join(f"<li>{escape(item)}</li>" for item in data["skills"])

    leadership_html = "\n".join(
        f"""
          <article class="service-card">
            <h3>{escape(item['title'])}</h3>
            <p>{escape(item['body'])}</p>
          </article>
        """.rstrip()
        for item in data["leadership_cards"]
    )

    generated_label = date.fromisoformat(data["generated_on"]).strftime("%B %d, %Y")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape(person['name'])} | Instructional Technology Researcher</title>
  <meta
    name="description"
    content="Academic portfolio for {escape(person['name'])}, Ph.D. candidate in Instructional Technology at the University of Alabama."
  >
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link
    href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=Manrope:wght@400;500;600;700;800&display=swap"
    rel="stylesheet"
  >
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <div class="page-shell">
    <header class="site-header">
      <a class="wordmark" href="#top">IDA</a>
      <nav class="site-nav" aria-label="Primary navigation">
        <a href="#about">About</a>
        <a href="#research">Research</a>
        <a href="#experience">Experience</a>
        <a href="#outputs">Outputs</a>
        <a href="#service">Service</a>
      </nav>
      <a class="button button-outline" href="{escape(data['source_file'])}">Download CV</a>
    </header>

    <main id="top">
      <section class="hero">
        <div class="hero-copy">
          <p class="eyebrow">Instructional Technology • Immersive Learning • AI in Education</p>
          <h1>{escape(person['name'])}</h1>
          <p class="hero-summary">{escape(data['profile_summary'])}</p>
          <div class="hero-actions">
            <a class="button" href="mailto:{escape(person['email'])}">Email David</a>
            <a class="button button-outline" href="#outputs">View Research</a>
          </div>
          <dl class="contact-grid" aria-label="Contact details">
            <div>
              <dt>Location</dt>
              <dd>{escape(person['location'])}</dd>
            </div>
            <div>
              <dt>Email</dt>
              <dd><a href="mailto:{escape(person['email'])}">{escape(person['email'])}</a></dd>
            </div>
            <div>
              <dt>Phone</dt>
              <dd><a href="tel:{escape(person['phone_href'])}">{escape(person['phone'])}</a></dd>
            </div>
            <div>
              <dt>Expected Ph.D.</dt>
              <dd>{escape(person['expected_phd'])}</dd>
            </div>
          </dl>
        </div>
        <aside class="hero-card">
          <p class="card-label">Current focus</p>
          <ul class="focus-list">
            <li>{escape(data['research_themes'][0]['title'])}: {escape(data['research_themes'][0]['body'])}</li>
            <li>{escape(data['research_themes'][2]['title'])}: {escape(data['research_themes'][2]['body'])}</li>
            <li>{escape(data['research_themes'][3]['title'])}: {escape(data['research_themes'][3]['body'])}</li>
          </ul>
          <div class="accent-stat">
            <span>Source of truth</span>
            <strong>{escape(data['source_file'])}</strong>
          </div>
        </aside>
      </section>

      <section class="metrics">
{metrics_html}
      </section>

      <section class="section" id="about">
        <div class="section-heading">
          <p class="eyebrow">About</p>
          <h2>Researcher, educator, and instructional designer</h2>
        </div>
        <div class="two-column">
          <div class="panel">
            <p>{escape(data['profile_summary'])}</p>
            <p>
              This website is regenerated from the Word CV directly, so future updates can begin in the
              CV and flow back into the web version through the build script.
            </p>
          </div>
          <div class="panel">
            <h3>Education</h3>
            <div class="mini-timeline">
{education_html}
            </div>
          </div>
        </div>
      </section>

      <section class="section" id="research">
        <div class="section-heading">
          <p class="eyebrow">Research Agenda</p>
          <h2>Designing immersive and AI-enabled learning for real impact</h2>
        </div>
        <div class="card-grid">
{research_themes_html}
        </div>
      </section>

      <section class="section" id="experience">
        <div class="section-heading">
          <p class="eyebrow">Experience</p>
          <h2>Selected roles generated from the CV source file</h2>
        </div>
        <div class="timeline">
{experience_html}
        </div>
      </section>

      <section class="section section-split" id="outputs">
        <div class="section-heading">
          <p class="eyebrow">Selected Outputs</p>
          <h2>A research record spanning journals, presentations, grants, and design practice</h2>
        </div>
        <div class="two-column">
          <div class="panel">
            <h3>Selected publications</h3>
            <ul class="feature-list">
{publications_html}
            </ul>
            <a class="text-link" href="{escape(data['source_file'])}">See the full publication list in the CV</a>
          </div>
          <div class="panel">
            <h3>Recent presentations</h3>
            <ul class="feature-list">
{presentations_html}
            </ul>
          </div>
        </div>
        <div class="two-column">
          <div class="panel">
            <h3>Grants and recognition</h3>
            <ul class="feature-list">
{grants_html}
            </ul>
          </div>
          <div class="panel">
            <h3>Skills and tools</h3>
            <ul class="tag-list" aria-label="Skills">
{skill_tags_html}
            </ul>
          </div>
        </div>
      </section>

      <section class="section" id="service">
        <div class="section-heading">
          <p class="eyebrow">Leadership & Service</p>
          <h2>Academic citizenship, mentoring, and community impact</h2>
        </div>
        <div class="card-grid">
{leadership_html}
        </div>
      </section>

      <section class="section cta">
        <div>
          <p class="eyebrow">Workflow</p>
          <h2>Generated from {escape(data['source_file'])} on {escape(generated_label)}</h2>
        </div>
        <div class="cta-actions">
          <a class="button" href="mailto:{escape(person['email'])}">Start a conversation</a>
          <a class="button button-outline" href="{escape(data['source_file'])}">Open full CV</a>
        </div>
      </section>
    </main>
  </div>
</body>
</html>
"""


def render_list_items(items: list[str]) -> str:
    return "\n".join(f"              <li>{escape(item)}</li>" for item in items)


def escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


def write_outputs(data: dict[str, Any]) -> None:
    rendered_html = render_html(data)
    OUTPUT_HTML.write_text(rendered_html, encoding="utf-8")
    OUTPUT_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    DIST_DIR.mkdir(exist_ok=True)
    DIST_HTML.write_text(rendered_html, encoding="utf-8")
    DIST_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    shutil.copy2(STYLESHEET, DIST_STYLES)
    shutil.copy2(SOURCE_DOCX, DIST_DOCX)
    NOJEKYLL.write_text("", encoding="utf-8")


def main() -> None:
    data = build_site_data()
    write_outputs(data)
    print(f"Built website from {SOURCE_DOCX.name} into {OUTPUT_HTML.name} and {DIST_DIR.name}/")


if __name__ == "__main__":
    main()
