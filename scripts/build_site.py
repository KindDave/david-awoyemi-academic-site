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
    r"^\d{4},\s*\d{4}$",
    r"^\d{4}$",
    r"^\d{1,2}/\d{4}\s*[-–]\s*\d{1,2}/\d{4}$",
    r"^\d{1,2}/\d{4}\s*[-–]\s*(Present|\d{1,2}/\d{4})$",
    r"^\d{1,2}/\d{1,2}/\d{4}$",
    r"^\d{1,2}/\d{1,2}/\d{4}\s*[-–]\s*\d{1,2}/\d{1,2}/\d{4}$",
    r"^[A-Za-z]+\s+\d{4}$",
    r"^[A-Za-z]+\s+\d{1,2},\s*\d{4}$",
    r"^[A-Za-z]+\s+\d{1,2}[–-]\d{1,2},\s*\d{4}$",
    r"^[A-Za-z]+\s+\d{1,2}[–-]\d{1,2},\s*\d{4}\.$",
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
    "Pepperdine",
)

PUBLICATION_SUBHEADINGS = {
    "Peer-reviewed Journal Articles",
    "Referred Conference Proceedings",
    "Book Chapters",
}

SERVICE_SUBHEADINGS = {
    "Journal Reviews",
    "Conference Chair and Discussant",
    "Conference Reviews",
    "Mentoring",
    "Community/Outreach/ Conferences Services",
}


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


def remove_reference_prefix(text: str) -> str:
    return re.sub(r"^\[\d+\]\s*", "", text).strip()


def truncate_text(text: str, limit: int = 210) -> str:
    cleaned = normalize_whitespace(text)
    if len(cleaned) <= limit:
        return cleaned
    shortened = cleaned[: limit - 3].rsplit(" ", 1)[0]
    return f"{shortened}..."


def split_on_numbered_items(line: str) -> list[str]:
    normalized = re.sub(r"\s(?=(?:\[\d+\]|\d+\]))", "\n", line)
    return [part.strip() for part in normalized.splitlines() if part.strip()]


def list_items(lines: list[str]) -> list[str]:
    items: list[str] = []
    buffer = ""
    for line in lines:
        for part in split_on_numbered_items(line):
            chunk = part
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


def group_subsections(lines: list[str], headings: set[str]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    current = "default"
    grouped[current] = []

    for line in lines:
        if line in headings:
            current = line
            grouped[current] = []
            continue
        grouped.setdefault(current, []).append(line)

    return grouped


def parse_named_date_pairs(lines: list[str]) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    index = 0
    while index < len(lines):
        name = lines[index]
        next_line = lines[index + 1] if index + 1 < len(lines) else ""
        if is_date_line(next_line):
            items.append({"name": name, "date": next_line.rstrip(".")})
            index += 2
        else:
            items.append({"name": name, "date": ""})
            index += 1
    return items


def split_entry_blocks(lines: list[str]) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    current_lines: list[str] = []

    for line in lines:
        if is_date_line(line):
            if current_lines:
                blocks.append({"date": line.rstrip("."), "lines": current_lines[:]})
                current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        blocks.append({"date": "", "lines": current_lines[:]})

    return blocks


def looks_like_org_line(text: str) -> bool:
    if not text:
        return False
    if text.endswith("."):
        return False
    return any(hint in text for hint in ORG_HINTS)


def split_inline_title_org(text: str) -> tuple[str, str]:
    if " — " in text:
        left, right = text.split(" — ", 1)
        return left.strip(), right.strip()
    if text.count(",") >= 1:
        first, remainder = text.split(",", 1)
        if len(first.strip()) < 55:
            return first.strip(), remainder.strip()
    return text.strip(), ""


def parse_entry_block(block: dict[str, Any]) -> dict[str, Any] | None:
    lines = block["lines"]
    if not lines:
        return None

    raw_title = lines[0]
    title, inline_org = split_inline_title_org(raw_title)
    organization = inline_org
    details_start = 1

    if len(lines) > 1 and looks_like_org_line(lines[1]):
        organization = lines[1]
        details_start = 2

    details = [line for line in lines[details_start:] if line]
    summary = truncate_text(" ".join(details), 220)

    return {
        "title": title,
        "organization": organization,
        "date": block["date"] or "Selected role",
        "details": details,
        "summary": summary,
    }


def parse_entries(lines: list[str]) -> list[dict[str, Any]]:
    entries = [parse_entry_block(block) for block in split_entry_blocks(lines)]
    return [entry for entry in entries if entry]


def parse_skills(lines: list[str]) -> list[dict[str, Any]]:
    skills: list[dict[str, Any]] = []
    index = 0
    while index < len(lines):
        category = lines[index]
        details = lines[index + 1] if index + 1 < len(lines) else ""
        items = [item.strip() for item in details.split(",") if item.strip()]
        skills.append(
            {
                "category": category,
                "details": details,
                "items": items[:5],
            }
        )
        index += 2
    return skills


def parse_citation(citation: str, kind_label: str) -> dict[str, str]:
    cleaned = remove_reference_prefix(citation)
    status = ""
    parentheticals = re.findall(r"\(([^)]+)\)", cleaned)
    for candidate in parentheticals:
        lowered = candidate.lower()
        if any(keyword in lowered for keyword in ("under review", "accepted", "submitted", "revision", "in press")):
            status = candidate
            break
    if not status:
        year_match = re.search(r"\b(20\d{2}|19\d{2})\b", cleaned)
        status = year_match.group(1) if year_match else kind_label

    title = cleaned
    context = ""
    match = re.search(r"\)\.\s*(.+)", cleaned)
    if match:
        remainder = match.group(1).strip()
        parts = [part.strip() for part in remainder.split(". ") if part.strip()]
        if parts:
            title = parts[0].rstrip(".")
            if len(parts) > 1:
                context = parts[1].split("https://")[0].split("Manuscript")[0].strip().rstrip(".").rstrip("(").strip()

    return {
        "title": title,
        "context": context or kind_label,
        "status": status,
    }


def is_showcase_role(entry: dict[str, Any]) -> bool:
    title = entry["title"].strip()
    if not title:
        return False
    if title.endswith("."):
        return False
    if len(title) > 70:
        return False
    if title.lower().startswith(("research on ", "analysis of ", "collection, ")):
        return False
    return True


def summarize_grant(text: str) -> dict[str, str]:
    cleaned = remove_reference_prefix(text)
    title, remainder = (cleaned.split(". ", 1) + [""])[:2]
    status = "Grant or fellowship"
    if "[Awarded]" in cleaned or "FUNDED" in cleaned:
        status = "Funded"
    elif "Nominee" in cleaned:
        status = "Nominee"
    elif "Applicant" in cleaned:
        status = "Applicant"
    elif "Resubmission" in cleaned:
        status = "Resubmission"
    return {
        "title": title.strip(),
        "context": remainder.strip() or "Grant or fellowship",
        "status": status,
    }


def summarize_service_items(items: list[dict[str, str]], limit: int = 3) -> str:
    if not items:
        return ""
    names = [item["name"] for item in items[:limit]]
    summary = ", ".join(names)
    if len(items) > limit:
        summary = f"{summary}, and more."
    return summary


def build_site_data() -> dict[str, Any]:
    paragraphs = read_docx_paragraphs(SOURCE_DOCX)
    header, sections = split_sections(paragraphs)

    publications_grouped = group_subsections(sections.get("PUBLICATIONS", []), PUBLICATION_SUBHEADINGS)
    service_grouped = group_subsections(sections.get("PROFESSIONAL AND COMMUNITY SERVICE", []), SERVICE_SUBHEADINGS)

    journal_articles = list_items(publications_grouped.get("Peer-reviewed Journal Articles", []))
    conference_presentations = list_items(sections.get("CONFERENCE PRESENTATIONS", []))
    grants = [remove_reference_prefix(line) for line in sections.get("GRANTS", [])]
    research_entries = parse_entries(sections.get("RESEARCH EXPERIENCE", []))
    teaching_entries = parse_entries(sections.get("TEACHING EXPERIENCE", []))
    design_entries = parse_entries(sections.get("INSTRUCTIONAL DESIGN EXPERIENCE", []))
    leadership_entries = parse_entries(sections.get("LEADERSHIP ROLE AND SERVICES", []))
    awards = parse_named_date_pairs(sections.get("AWARDS & SCHOLARSHIPS", []))
    certifications = parse_named_date_pairs(sections.get("CERTIFICATIONS", []))
    skills = parse_skills(sections.get("TECHNICAL AND PROFESSIONAL SKILLS", []))
    affiliations = [{"name": item} for item in sections.get("PROFESSIONAL AFFLIATIONS", [])]

    service_journals = parse_named_date_pairs(service_grouped.get("Journal Reviews", []))
    service_reviews = parse_named_date_pairs(service_grouped.get("Conference Reviews", []))
    service_chairs = parse_named_date_pairs(service_grouped.get("Conference Chair and Discussant", []))
    service_mentoring = parse_named_date_pairs(service_grouped.get("Mentoring", []))
    service_outreach = parse_named_date_pairs(service_grouped.get("Community/Outreach/ Conferences Services", []))

    header_text = " ".join(header)
    email = extract_email(header_text)
    phone = extract_phone(header_text)

    stable_roles = [
        entry
        for entry in (research_entries + teaching_entries + design_entries)
        if "guest lecture" not in entry["title"].lower()
        and "workshop facilitator" not in entry["title"].lower()
        and is_showcase_role(entry)
    ]
    featured_roles = stable_roles[:4]
    invited_talks = [entry for entry in teaching_entries if "guest" in entry["title"].lower()][:3]

    research_themes = [
        {
            "title": "Immersive Learning Systems",
            "body": "Designs immersive virtual reality experiences for engineering and STEM learning, with a focus on safety training, hazard identification, and applied multimedia learning.",
        },
        {
            "title": "Learning Analytics",
            "body": "Uses behavioral analytics, statistical modeling, and mixed methods to explain how learners engage, shift strategies, and demonstrate growth over time.",
        },
        {
            "title": "AI-Enhanced Education",
            "body": "Explores generative AI, AI literacy, adaptive systems, and AI-supported instructional design for teacher education, assessment, and digital learning environments.",
        },
        {
            "title": "Equity in STEM Participation",
            "body": "Advances broadening participation in computing and STEM through teacher development, inclusive learning design, and pathways for underrepresented learners.",
        },
    ]

    top_awards = awards[:4]
    hero_highlights = [award["name"] for award in top_awards[:3]]
    selected_publications = [parse_citation(item, "Journal article") for item in journal_articles[:6]]
    recent_presentations = [parse_citation(item, "Conference presentation") for item in conference_presentations[:4]]
    featured_grants = [summarize_grant(item) for item in grants[:4]]
    award_cards = [
        {"title": item["name"], "meta": item["date"] or "Recognition"}
        for item in top_awards
    ]
    certification_cards = [
        {"title": item["name"], "meta": item["date"] or "Certification"}
        for item in certifications[:4]
    ]

    service_cards = [
        {
            "eyebrow": "Journal Reviewing",
            "title": f"{len(service_journals)} review appointments",
            "body": summarize_service_items(service_journals),
        },
        {
            "eyebrow": "Conference Service",
            "title": f"{len(service_chairs) + len(service_reviews)} chairing and review roles",
            "body": summarize_service_items(service_chairs + service_reviews),
        },
        {
            "eyebrow": "Mentoring",
            "title": f"{len(service_mentoring)} mentoring initiatives",
            "body": summarize_service_items(service_mentoring),
        },
        {
            "eyebrow": "Community Engagement",
            "title": f"{len(service_outreach)} outreach and campus contributions",
            "body": summarize_service_items(service_outreach),
        },
    ]

    profile_summary = sections.get("PROFILE SUMMARY", [""])[0]
    primary_skill_tags = [item for skill in skills[:3] for item in skill["items"][:3]][:9]

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
        "profile_summary": profile_summary,
        "education": parse_education(sections.get("EDUCATION", [])),
        "hero_highlights": hero_highlights,
        "research_themes": research_themes,
        "metrics": [
            {"value": str(len(journal_articles)), "label": "journal articles and review-stage manuscripts"},
            {"value": str(len(conference_presentations)), "label": "conference presentations and accepted sessions"},
            {"value": str(len(grants)), "label": "grants, fellowships, and funded initiatives"},
            {"value": str(len(awards)), "label": "awards and scholarships listed in the CV"},
        ],
        "featured_roles": featured_roles,
        "invited_talks": invited_talks,
        "selected_publications": selected_publications,
        "recent_presentations": recent_presentations,
        "featured_grants": featured_grants,
        "award_cards": award_cards,
        "certification_cards": certification_cards,
        "skills": skills,
        "primary_skill_tags": primary_skill_tags,
        "leadership_cards": leadership_entries[:4],
        "service_cards": service_cards,
        "affiliations": affiliations,
        "publications_breakdown": {
            key: [remove_reference_prefix(item) for item in list_items(value)]
            for key, value in publications_grouped.items()
            if key != "default"
        },
        "raw_sections": sections,
    }
    return data


def render_html(data: dict[str, Any]) -> str:
    person = data["person"]
    generated_label = date.fromisoformat(data["generated_on"]).strftime("%B %d, %Y")

    metrics_html = "\n".join(
        f"""
        <article class="metric-card">
          <strong>{escape(item['value'])}</strong>
          <span>{escape(item['label'])}</span>
        </article>
        """.rstrip()
        for item in data["metrics"]
    )

    highlight_html = "\n".join(
        f"<li>{escape(item)}</li>" for item in data["hero_highlights"]
    )

    theme_html = "\n".join(
        f"""
          <article class="research-card">
            <p class="card-kicker">Theme</p>
            <h3>{escape(item['title'])}</h3>
            <p>{escape(item['body'])}</p>
          </article>
        """.rstrip()
        for item in data["research_themes"]
    )

    education_html = "\n".join(
        f"""
          <article class="education-item">
            <span>{escape(item['date'])}</span>
            <strong>{escape(item['degree'])}</strong>
            <p>{escape(item['institution'])}</p>
          </article>
        """.rstrip()
        for item in data["education"]
    )

    role_html = "\n".join(
        f"""
          <article class="role-card">
            <div class="role-meta">{escape(item['date'])}</div>
            <h3>{escape(item['title'])}</h3>
            <p class="role-org">{escape(item['organization'])}</p>
            <p>{escape(item['summary'])}</p>
          </article>
        """.rstrip()
        for item in data["featured_roles"]
    )

    talk_html = "\n".join(
        f"""
          <article class="mini-card">
            <p class="mini-meta">{escape(item['date'])}</p>
            <h3>{escape(item['title'])}</h3>
            <p>{escape(item['organization'] or item['summary'])}</p>
          </article>
        """.rstrip()
        for item in data["invited_talks"]
    )

    publication_html = "\n".join(
        f"""
          <article class="output-card">
            <p class="mini-meta">{escape(item['status'])}</p>
            <h3>{escape(item['title'])}</h3>
            <p>{escape(item['context'])}</p>
          </article>
        """.rstrip()
        for item in data["selected_publications"]
    )

    presentation_html = "\n".join(
        f"""
          <article class="output-card">
            <p class="mini-meta">{escape(item['status'])}</p>
            <h3>{escape(item['title'])}</h3>
            <p>{escape(item['context'])}</p>
          </article>
        """.rstrip()
        for item in data["recent_presentations"]
    )

    grants_html = "\n".join(
        f"""
          <article class="output-card">
            <p class="mini-meta">{escape(item['status'])}</p>
            <h3>{escape(item['title'])}</h3>
            <p>{escape(item['context'])}</p>
          </article>
        """.rstrip()
        for item in data["featured_grants"]
    )

    awards_html = "\n".join(
        f"""
          <article class="compact-card">
            <h3>{escape(item['title'])}</h3>
            <p>{escape(item['meta'])}</p>
          </article>
        """.rstrip()
        for item in data["award_cards"]
    )

    certifications_html = "\n".join(
        f"""
          <article class="compact-card">
            <h3>{escape(item['title'])}</h3>
            <p>{escape(item['meta'])}</p>
          </article>
        """.rstrip()
        for item in data["certification_cards"]
    )

    skill_panel_html = "\n".join(
        f"""
          <article class="skill-panel">
            <h3>{escape(item['category'])}</h3>
            <p>{escape(truncate_text(item['details'], 220))}</p>
          </article>
        """.rstrip()
        for item in data["skills"]
    )

    skill_tags_html = "\n".join(f"<li>{escape(item)}</li>" for item in data["primary_skill_tags"])

    leadership_html = "\n".join(
        f"""
          <article class="mini-card">
            <p class="mini-meta">{escape(item['date'])}</p>
            <h3>{escape(item['title'])}</h3>
            <p>{escape(item['organization'] or item['summary'])}</p>
          </article>
        """.rstrip()
        for item in data["leadership_cards"]
    )

    service_html = "\n".join(
        f"""
          <article class="service-card">
            <p class="card-kicker">{escape(item['eyebrow'])}</p>
            <h3>{escape(item['title'])}</h3>
            <p>{escape(item['body'])}</p>
          </article>
        """.rstrip()
        for item in data["service_cards"]
    )

    affiliation_html = "\n".join(
        f"<li>{escape(item['name'])}</li>" for item in data["affiliations"]
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape(person['name'])} | Instructional Technology Researcher</title>
  <meta
    name="description"
    content="Academic portfolio for {escape(person['name'])}, doctoral researcher in Instructional Technology at the University of Alabama."
  >
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link
    href="https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700;800&family=Newsreader:opsz,wght@6..72,500;6..72,700&display=swap"
    rel="stylesheet"
  >
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <div class="site-bg"></div>
  <div class="page-shell">
    <header class="site-header">
      <a class="brand" href="#top">
        <span class="brand-mark">IDA</span>
        <span class="brand-text">David Awoyemi</span>
      </a>
      <nav class="site-nav" aria-label="Primary navigation">
        <a href="#about">About</a>
        <a href="#research">Research</a>
        <a href="#work">Work</a>
        <a href="#outputs">Outputs</a>
        <a href="#service">Service</a>
      </nav>
      <a class="button button-outline" href="{escape(data['source_file'])}">Download CV</a>
    </header>

    <main id="top">
      <section class="hero">
        <div class="hero-main">
          <p class="eyebrow">Instructional Technology • Immersive Learning • AI in Education</p>
          <h1>{escape(person['name'])}</h1>
          <p class="hero-lede">{escape(data['profile_summary'])}</p>
          <p class="hero-affiliation">{escape(person['affiliation'])}</p>
          <div class="hero-actions">
            <a class="button" href="mailto:{escape(person['email'])}">Contact David</a>
            <a class="button button-outline" href="#outputs">Explore Research</a>
          </div>
          <ul class="highlight-list">
{highlight_html}
          </ul>
        </div>
        <aside class="hero-side">
          <div class="hero-panel">
            <p class="card-kicker">Current Base</p>
            <h2>University of Alabama</h2>
            <dl class="contact-grid">
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
          <div class="hero-panel source-panel">
            <p class="card-kicker">Source of Truth</p>
            <h3>{escape(data['source_file'])}</h3>
            <p>This website is regenerated directly from the Word CV through the local build script and GitHub deployment workflow.</p>
          </div>
        </aside>
      </section>

      <section class="metrics">
{metrics_html}
      </section>

      <section class="section about" id="about">
        <div class="section-heading">
          <p class="eyebrow">About</p>
          <h2>Research, teaching, and design work shaped for equitable learning.</h2>
        </div>
        <div class="about-grid">
          <div class="panel prose-panel">
            <p>{escape(data['profile_summary'])}</p>
            <p>David’s work sits at the intersection of immersive learning systems, AI-enhanced pedagogy, analytics, and inclusive STEM participation. His projects span engineering education, teacher development, digital course design, and student support.</p>
          </div>
          <div class="panel">
            <h3>Education</h3>
            <div class="education-list">
{education_html}
            </div>
          </div>
        </div>
      </section>

      <section class="section" id="research">
        <div class="section-heading">
          <p class="eyebrow">Research Agenda</p>
          <h2>Four strands organize the portfolio and the questions behind it.</h2>
        </div>
        <div class="research-grid">
{theme_html}
        </div>
      </section>

      <section class="section" id="work">
        <div class="section-heading">
          <p class="eyebrow">Core Roles</p>
          <h2>Selected academic and instructional roles drawn from the CV.</h2>
        </div>
        <div class="role-grid">
{role_html}
        </div>
        <div class="subsection">
          <div class="subsection-heading">
            <h3>Invited Teaching and Talks</h3>
            <a class="text-link" href="#outputs">See research outputs</a>
          </div>
          <div class="mini-grid">
{talk_html}
          </div>
        </div>
      </section>

      <section class="section" id="outputs">
        <div class="section-heading">
          <p class="eyebrow">Selected Outputs</p>
          <h2>Recent publications, presentations, grants, and recognitions.</h2>
        </div>
        <div class="subsection">
          <div class="subsection-heading">
            <h3>Publications</h3>
            <a class="text-link" href="{escape(data['source_file'])}">Full list in CV</a>
          </div>
          <div class="output-grid">
{publication_html}
          </div>
        </div>
        <div class="subsection">
          <div class="subsection-heading">
            <h3>Recent Presentations</h3>
          </div>
          <div class="output-grid">
{presentation_html}
          </div>
        </div>
        <div class="subsection split-subsection">
          <div class="panel">
            <div class="subsection-heading">
              <h3>Grants and Fellowships</h3>
            </div>
            <div class="stack-grid">
{grants_html}
            </div>
          </div>
          <div class="panel">
            <div class="subsection-heading">
              <h3>Awards and Certifications</h3>
            </div>
            <div class="compact-grid">
{awards_html}
{certifications_html}
            </div>
          </div>
        </div>
      </section>

      <section class="section" id="service">
        <div class="section-heading">
          <p class="eyebrow">Leadership, Skills, and Service</p>
          <h2>Academic citizenship alongside digital learning craft.</h2>
        </div>
        <div class="split-subsection">
          <div class="panel">
            <div class="subsection-heading">
              <h3>Leadership Roles</h3>
            </div>
            <div class="mini-grid">
{leadership_html}
            </div>
          </div>
          <div class="panel">
            <div class="subsection-heading">
              <h3>Service Snapshot</h3>
            </div>
            <div class="service-grid">
{service_html}
            </div>
          </div>
        </div>
        <div class="split-subsection">
          <div class="panel">
            <div class="subsection-heading">
              <h3>Skill Areas</h3>
            </div>
            <ul class="tag-list">
{skill_tags_html}
            </ul>
            <div class="skill-grid">
{skill_panel_html}
            </div>
          </div>
          <div class="panel">
            <div class="subsection-heading">
              <h3>Professional Affiliations</h3>
            </div>
            <ul class="affiliation-list">
{affiliation_html}
            </ul>
          </div>
        </div>
      </section>

      <section class="section cta">
        <div>
          <p class="eyebrow">Workflow</p>
          <h2>Generated from {escape(data['source_file'])} on {escape(generated_label)}</h2>
          <p>Update the Word CV, rebuild locally, and push to GitHub to publish a fresh version automatically.</p>
        </div>
        <div class="hero-actions">
          <a class="button" href="mailto:{escape(person['email'])}">Start a conversation</a>
          <a class="button button-outline" href="{escape(data['source_file'])}">Open full CV</a>
        </div>
      </section>
    </main>
  </div>
</body>
</html>
"""


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
