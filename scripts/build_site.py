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
OUTPUT_JSON = ROOT / "site-data.json"
DIST_DIR = ROOT / "dist"
NOJEKYLL = DIST_DIR / ".nojekyll"

ROOT_SHARED_CSS = ROOT / "shared.css"
ROOT_SHARED_JS = ROOT / "shared.js"
ROOT_STYLES = ROOT / "styles.css"
ASSET_DIR = ROOT / "assets"
DIST_ASSET_DIR = DIST_DIR / "assets"

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

PROFILE_LINKS = [
    {
        "label": "Google Scholar",
        "url": "https://scholar.google.com/citations?user=NIWz8s4AAAAJ&hl=en",
        "description": "Citation record, papers, and scholarly impact.",
    },
    {
        "label": "ResearchGate",
        "url": "https://www.researchgate.net/profile/Idowu-Awoyemi-2",
        "description": "Research profile, project activity, and collaborations.",
    },
    {
        "label": "ADIE Lab",
        "url": "https://sites.ua.edu/adielab/people/",
        "description": "University of Alabama lab home and research context.",
    },
    {
        "label": "Full CV",
        "url": SOURCE_DOCX.name,
        "description": "Download the current Word CV that drives this site.",
    },
]

HERO_HEADSHOT = {
    "src": "assets/images/headshot-main.png",
    "alt": "Professional headshot of David Awoyemi",
}

HOME_RESEARCH_PRACTICE = [
    {
        "src": "assets/images/home-vr-safety.jpg",
        "alt": "Immersive VR construction safety simulation",
        "caption": "XR safety training research",
    },
    {
        "src": "assets/images/home-ai-literacy.jpg",
        "alt": "AI literacy story characters graphic",
        "caption": "AI literacy curriculum design",
    },
    {
        "src": "assets/images/home-research-team.jpg",
        "alt": "Research team slide showing project members",
        "caption": "Collaborative research teams",
    },
]

ACADEMIC_MEDIA = [
    {
        "src": "assets/images/headshot-stage.jpg",
        "alt": "David Awoyemi presenting at a conference podium",
        "caption": "Conference and scholarly presentation",
    },
    {
        "src": "assets/images/academic-schedule.jpg",
        "alt": "Code-N-Sensor camp schedule",
        "caption": "Program and curriculum planning",
    },
    {
        "src": "assets/images/academic-boris.jpg",
        "alt": "BORIS software overview slide",
        "caption": "Behavioral observation and analytics",
    },
    {
        "src": "assets/images/academic-workshop.jpg",
        "alt": "Behavioral and microgenetic analysis workshop cover",
        "caption": "Workshop and scholarly dissemination",
    },
]

AFFILIATION_DETAILS = {
    "AERA": "American Educational Research Association",
    "AECT": "Association for Educational Communications and Technology",
    "iLRN": "Immersive Learning Research Network",
    "ACM": "Association for Computing Machinery",
    "NIM": "Nigerian Institute of Management",
    "TRCN": "Teachers Registration Council of Nigeria",
}

RESEARCH_CASE_STUDIES = [
    {
        "number": "01",
        "label": "Immersive STEM Learning",
        "title": "AI-Enhanced XR Learning for STEM Education: VR Hazard Identification in Civil Engineering",
        "subtitle": "University of Alabama · Civil engineering safety training · Mixed-methods design and analytics",
        "tags": [
            "XR Learning",
            "Virtual Reality",
            "Engineering Education",
            "Safety Training",
            "Learning Analytics",
        ],
        "problem": "Construction safety instruction often depends on low-immersion demonstrations that make hazard recognition difficult to practice authentically before students enter high-risk settings.",
        "stakeholders": [
            "Civil engineering students and instructors",
            "Lab researchers designing VR learning tasks",
            "Programs preparing students for safety-critical work",
        ],
        "frameworks": [
            "Multimedia learning and immersive cognition principles",
            "Design-based research for iterative refinement",
            "Performance-centered assessment for hazard identification",
        ],
        "methods": [
            "VR simulation design",
            "Behavioral analytics",
            "Microgenetic analysis",
            "Bayesian cognitive diagnostics",
        ],
        "solution": "The project uses generative-AI-supported virtual environments and structured hazard-identification tasks to study how learners notice risks, shift strategies, and develop safer decision patterns in authentic contexts.",
        "outcomes": [
            "Produced publishable work on immersive technology-enhanced learning and safety training.",
            "Strengthened a research program connecting XR design with measurable performance evidence.",
        ],
        "reflection": "This case anchors a broader research direction: immersive environments become more valuable when they are not only engaging, but also analytically transparent enough to reveal how expertise develops over time.",
        "images": [
            {
                "src": "assets/images/research-case1-1.jpeg",
                "alt": "VR hazard identification scenario with construction site",
            },
            {
                "src": "assets/images/research-case1-2.jpeg",
                "alt": "Night scaffold hazard markers in VR environment",
            },
            {
                "src": "assets/images/research-case1-3.jpeg",
                "alt": "AI avatar in immersive safety training environment",
            },
        ],
    },
    {
        "number": "02",
        "label": "AI Literacy Curriculum",
        "title": "AI-WISE: Industry-Informed Artificial Intelligence Literacy Curriculum for Higher Education",
        "subtitle": "University of Alabama · Undergraduate AI literacy design · Cross-disciplinary curriculum development",
        "tags": [
            "AI Literacy",
            "Curriculum Design",
            "Higher Education",
            "Workforce Readiness",
            "Equity",
        ],
        "problem": "Students increasingly encounter AI tools in academic and professional settings, yet many programs still lack structured, ethical, and workforce-relevant AI literacy experiences.",
        "stakeholders": [
            "Undergraduate students across disciplines",
            "Faculty embedding AI in coursework",
            "Industry partners shaping competency expectations",
        ],
        "frameworks": [
            "Backward design for outcome-aligned curriculum planning",
            "Universal Design for Learning for multimodal access",
            "Culturally responsive pedagogy for inclusive participation",
        ],
        "methods": [
            "Industry competency mapping",
            "Co-design workshops",
            "Pilot curriculum implementation",
            "Feedback and thematic analysis",
        ],
        "solution": "AI-WISE organizes practical AI skills, ethical reasoning, and reflective evaluation into modular learning experiences that faculty can adapt without needing deep technical specialization.",
        "outcomes": [
            "Created a reusable curriculum model for broader AI literacy integration.",
            "Supported conference dissemination around practical and equitable AI education design.",
        ],
        "reflection": "The strongest lesson here is that AI literacy is not only about tools. It is about helping learners interpret, question, and apply AI systems responsibly in disciplinary and civic contexts.",
        "images": [
            {
                "src": "assets/images/research-case2-1.jpg",
                "alt": "Illustrated AI literacy story characters and robot",
            },
            {
                "src": "assets/images/research-case2-2.jpg",
                "alt": "Code-N-Sensor camp weekly schedule",
            },
            {
                "src": "assets/images/research-case2-3.jpg",
                "alt": "Research team image for project collaboration",
            },
        ],
    },
    {
        "number": "03",
        "label": "Physiological Learning Analytics",
        "title": "Beyond Self-Report: Using Eye-Tracking and Physiological Data to Evaluate Learning in Computing Environments",
        "subtitle": "NSF ITEST context · Elementary computing experiences · Multimodal evaluation and broadening participation",
        "tags": [
            "Eye-Tracking",
            "Physiological Computing",
            "Elementary STEM",
            "Evaluation",
            "Mixed Methods",
        ],
        "problem": "Traditional evaluation methods often miss moment-to-moment evidence of attention, cognitive load, and engagement, especially with younger learners who may not fully articulate what they experienced.",
        "stakeholders": [
            "Elementary learners in computing activities",
            "Researchers collecting multimodal evidence",
            "Programs focused on equitable STEM pathways",
        ],
        "frameworks": [
            "Mixed-methods evaluation design",
            "Cognitive load theory",
            "Learning analytics for multimodal evidence integration",
        ],
        "methods": [
            "Eye-tracking and pupil-dilation analysis",
            "Physiological sensing",
            "Cross-case comparison",
            "Quantitative and qualitative synthesis",
        ],
        "solution": "This work integrates physiological and behavioral data with more familiar assessments to create a richer view of how learners experience computing tasks and where instructional support is needed.",
        "outcomes": [
            "Contributed to NSF-supported research on computing participation and learner experience.",
            "Extended evaluation practice beyond self-report toward more responsive evidence models.",
        ],
        "reflection": "The project reinforced an important design belief: evaluation should not be an afterthought. It should be built into how we understand learning as it unfolds, especially in novel technology environments.",
        "images": [
            {
                "src": "assets/images/research-case3-1.jpg",
                "alt": "BORIS software overview slide",
            },
            {
                "src": "assets/images/research-case3-2.jpg",
                "alt": "Instructional technology documentation and training workshop cover",
            },
            {
                "src": "assets/images/research-case3-3.jpg",
                "alt": "Behavioral and microgenetic analysis workshop slide cover",
            },
        ],
    },
]

SHARED_CSS = """@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Lora:wght@400;500;600;700&display=swap');

*, *::before, *::after { box-sizing: border-box; }
html { scroll-behavior: smooth; }

:root {
  color-scheme: light;
  --bg: #f5f8ff;
  --bg2: #eaf0fb;
  --bg3: #dfe7f6;
  --card: rgba(255, 255, 255, 0.88);
  --card-strong: #ffffff;
  --navy: #0f2d6b;
  --navy2: #1f4ba3;
  --navy-soft: rgba(15, 45, 107, 0.08);
  --gold: #c3902f;
  --text1: #081225;
  --text2: #2d3a59;
  --text3: #65759a;
  --border: rgba(15, 45, 107, 0.11);
  --border-strong: rgba(15, 45, 107, 0.2);
  --nav-bg: rgba(245, 248, 255, 0.88);
  --shadow: 0 18px 50px rgba(15, 45, 107, 0.08);
  --shadow-strong: 0 24px 70px rgba(15, 45, 107, 0.14);
}

[data-theme="dark"] {
  color-scheme: dark;
  --bg: #04101f;
  --bg2: #09192e;
  --bg3: #0d2441;
  --card: rgba(10, 22, 43, 0.88);
  --card-strong: #08162d;
  --navy: #8bb4ff;
  --navy2: #b4ccff;
  --navy-soft: rgba(139, 180, 255, 0.12);
  --gold: #f0c76a;
  --text1: #f1f5ff;
  --text2: #d2dbf0;
  --text3: #93a4c8;
  --border: rgba(139, 180, 255, 0.14);
  --border-strong: rgba(139, 180, 255, 0.24);
  --nav-bg: rgba(4, 16, 31, 0.88);
  --shadow: 0 18px 50px rgba(0, 0, 0, 0.34);
  --shadow-strong: 0 24px 70px rgba(0, 0, 0, 0.44);
}

body {
  margin: 0;
  min-width: 320px;
  background:
    radial-gradient(circle at top left, rgba(31, 75, 163, 0.14), transparent 34%),
    radial-gradient(circle at top right, rgba(195, 144, 47, 0.12), transparent 28%),
    linear-gradient(180deg, var(--bg), var(--bg2) 54%, var(--bg));
  color: var(--text1);
  font-family: 'Inter', system-ui, sans-serif;
  line-height: 1.72;
  transition: background 0.35s ease, color 0.35s ease;
  overflow-x: hidden;
}

a { color: inherit; }
img { max-width: 100%; display: block; }

#particles {
  position: fixed;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
}

.page-shell,
.site-footer {
  position: relative;
  z-index: 1;
}

.site-nav {
  position: sticky;
  top: 0;
  z-index: 50;
  backdrop-filter: blur(18px) saturate(1.5);
  background: var(--nav-bg);
  border-bottom: 1px solid var(--border);
}

.nav-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0.95rem 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 0.85rem;
  text-decoration: none;
  min-width: 0;
}

.brand-mark {
  width: 2.75rem;
  height: 2.75rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: linear-gradient(135deg, var(--navy), var(--gold));
  color: white;
  font: 700 0.92rem 'Inter', system-ui, sans-serif;
  letter-spacing: 0.08em;
  box-shadow: var(--shadow);
}

.brand-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.brand-name {
  font: 600 1.02rem 'Lora', serif;
  letter-spacing: -0.02em;
}

.brand-subtitle {
  font-size: 0.74rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text3);
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  list-style: none;
  padding: 0;
  margin: 0;
}

.nav-links a {
  text-decoration: none;
  color: var(--text2);
  font-size: 0.9rem;
  font-weight: 600;
  padding: 0.6rem 0.85rem;
  border-radius: 999px;
  transition: background 0.2s ease, color 0.2s ease, transform 0.2s ease;
}

.nav-links a:hover,
.nav-links a.is-active {
  color: var(--navy);
  background: var(--navy-soft);
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.theme-toggle,
.mobile-theme-toggle {
  appearance: none;
  border: 1px solid var(--border-strong);
  background: var(--card);
  color: var(--text1);
  border-radius: 999px;
  padding: 0.55rem 0.95rem;
  font: 600 0.85rem 'Inter', system-ui, sans-serif;
  cursor: pointer;
}

.nav-cta,
.button,
.button-secondary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  text-decoration: none;
  border-radius: 999px;
  padding: 0.9rem 1.3rem;
  font-weight: 700;
  transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease, color 0.2s ease;
}

.nav-cta,
.button {
  color: white;
  background: linear-gradient(135deg, var(--navy), var(--navy2));
  box-shadow: var(--shadow);
}

.button-secondary {
  color: var(--text1);
  background: transparent;
  border: 1px solid var(--border-strong);
}

.nav-cta:hover,
.button:hover,
.button-secondary:hover {
  transform: translateY(-1px);
}

.hamburger {
  display: none;
  width: 2.6rem;
  height: 2.6rem;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 0.28rem;
  appearance: none;
  border: 1px solid var(--border);
  background: var(--card);
  border-radius: 0.85rem;
  cursor: pointer;
}

.hamburger span {
  display: block;
  width: 1.1rem;
  height: 2px;
  border-radius: 999px;
  background: var(--text1);
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.hamburger.is-open span:nth-child(1) { transform: translateY(0.4rem) rotate(45deg); }
.hamburger.is-open span:nth-child(2) { opacity: 0; }
.hamburger.is-open span:nth-child(3) { transform: translateY(-0.4rem) rotate(-45deg); }

.mobile-nav {
  display: none;
  position: fixed;
  inset: 4.9rem 1rem auto;
  z-index: 45;
  padding: 1rem;
  border-radius: 1.25rem;
  border: 1px solid var(--border);
  background: var(--card-strong);
  box-shadow: var(--shadow-strong);
}

.mobile-nav.is-open { display: block; }

.mobile-nav a {
  display: block;
  padding: 0.85rem 0.95rem;
  border-radius: 0.9rem;
  text-decoration: none;
  font-weight: 600;
  color: var(--text2);
}

.mobile-nav a.is-active,
.mobile-nav a:hover {
  color: var(--navy);
  background: var(--navy-soft);
}

.mobile-nav-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-top: 0.9rem;
}

.main-wrap {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1.5rem 5rem;
}

.hero {
  min-height: calc(100vh - 5.25rem);
  display: grid;
  grid-template-columns: 0.94fr 1.06fr;
  gap: 2.4rem;
  align-items: center;
  padding: 5rem 0 3.5rem;
}

.hero-photo {
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
  align-items: center;
}

.profile-photo-card {
  width: min(24rem, 100%);
  border-radius: 2rem;
  overflow: hidden;
  border: 1px solid var(--border);
  background: var(--card-strong);
  box-shadow: var(--shadow-strong);
}

.profile-photo-card img {
  width: 100%;
  display: block;
  aspect-ratio: 4 / 5;
  object-fit: cover;
  object-position: center top;
 }

.profile-monogram {
  width: min(24rem, 100%);
  aspect-ratio: 4 / 5;
  border-radius: 2rem;
  border: 1px solid var(--border);
  background:
    radial-gradient(circle at 20% 22%, rgba(195, 144, 47, 0.24), transparent 24%),
    linear-gradient(155deg, rgba(31, 75, 163, 0.22), transparent 48%),
    linear-gradient(180deg, var(--card-strong), rgba(255, 255, 255, 0.5));
  box-shadow: var(--shadow-strong);
  display: grid;
  place-items: center;
  overflow: hidden;
  position: relative;
}

.profile-monogram::after {
  content: "";
  position: absolute;
  inset: 1rem;
  border-radius: 1.4rem;
  border: 1px dashed var(--border-strong);
}

.profile-monogram strong {
  font: 600 clamp(3rem, 8vw, 5.5rem) 'Lora', serif;
  letter-spacing: -0.05em;
  color: var(--navy);
}

.profile-links-inline {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.75rem;
}

.hero-visual-grid,
.media-strip-grid,
.case-gallery {
  display: grid;
  gap: 0.85rem;
}

.hero-visual-grid {
  width: min(24rem, 100%);
  grid-template-columns: 1.2fr 0.8fr;
}

.hero-visual-grid .media-card:first-child {
  grid-row: span 2;
  min-height: 22rem;
}

.media-card {
  position: relative;
  overflow: hidden;
  border-radius: 1.25rem;
  border: 1px solid var(--border);
  box-shadow: var(--shadow);
  background: var(--card-strong);
}

.media-card img {
  width: 100%;
  height: 100%;
  min-height: 10rem;
  object-fit: cover;
  display: block;
}

.media-card figcaption {
  position: absolute;
  inset: auto 0 0 0;
  padding: 1rem 1rem 0.9rem;
  background: linear-gradient(180deg, transparent, rgba(5, 12, 26, 0.82));
  color: white;
  font-size: 0.84rem;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.pill-link {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.65rem 1rem;
  border-radius: 999px;
  text-decoration: none;
  border: 1px solid var(--border-strong);
  background: var(--card);
  color: var(--navy);
  font-weight: 700;
  font-size: 0.88rem;
}

.hero-copy {
  display: flex;
  flex-direction: column;
  gap: 1.15rem;
}

.eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 0.6rem;
  font-size: 0.76rem;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--navy);
}

.eyebrow::before {
  content: "";
  width: 1.8rem;
  height: 2px;
  border-radius: 999px;
  background: currentColor;
}

.hero h1,
.page-hero h1,
.section-heading h2,
.feature-title,
.strip-title,
.publication-year,
.case-title,
.footer-brand {
  font-family: 'Lora', serif;
  letter-spacing: -0.03em;
}

.hero h1 {
  font-size: clamp(2.9rem, 7vw, 5rem);
  line-height: 0.98;
  margin: 0;
}

.hero-role {
  font-size: clamp(1.02rem, 2.3vw, 1.35rem);
  color: var(--navy);
  font-weight: 700;
}

.hero-copy p {
  margin: 0;
  color: var(--text2);
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.8rem;
  padding-top: 0.4rem;
}

.highlight-list {
  display: grid;
  gap: 0.75rem;
  padding: 0;
  list-style: none;
  margin: 0.4rem 0 0;
  counter-reset: highlights;
}

.highlight-list li {
  display: flex;
  align-items: flex-start;
  gap: 0.7rem;
  padding: 0.9rem 1rem;
  border: 1px solid var(--border);
  border-radius: 1rem;
  background: var(--card);
  box-shadow: var(--shadow);
}

.highlight-list li::before {
  counter-increment: highlights;
  content: counter(highlights, decimal-leading-zero);
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  color: var(--navy);
  padding-top: 0.15rem;
}

.metrics-band {
  margin: 0 -1.5rem;
  padding: 0 1.5rem;
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
}

.metrics-grid {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
}

.metric-card {
  padding: 1.7rem 1.1rem;
  text-align: center;
  border-right: 1px solid var(--border);
}

.metric-card:last-child { border-right: 0; }

.metric-value {
  display: block;
  font: 600 clamp(2rem, 5vw, 2.6rem) 'Lora', serif;
  color: var(--navy);
  line-height: 1;
}

.metric-label {
  display: block;
  margin-top: 0.45rem;
  font-size: 0.7rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text3);
  font-weight: 800;
}

.page-hero {
  padding: 7rem 0 2.8rem;
  text-align: center;
}

.page-hero h1 {
  font-size: clamp(2.5rem, 6vw, 4.4rem);
  margin: 0.35rem 0 0.85rem;
}

.page-hero p {
  max-width: 48rem;
  margin: 0 auto;
  color: var(--text2);
}

.section {
  padding: 4.75rem 0;
}

.section-alt {
  margin: 0 -1.5rem;
  padding: 4.75rem 1.5rem;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.16), rgba(255, 255, 255, 0.02));
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
}

.section-inner {
  max-width: 1200px;
  margin: 0 auto;
}

.section-heading {
  max-width: 44rem;
  margin-bottom: 2.2rem;
}

.section-heading h2 {
  font-size: clamp(2rem, 4vw, 3rem);
  line-height: 1.06;
  margin: 0.35rem 0 0.8rem;
}

.section-heading p {
  margin: 0;
  color: var(--text2);
}

.grid-3,
.grid-4,
.profile-links-grid,
.interests-grid,
.awards-grid,
.feature-grid {
  display: grid;
  gap: 1.25rem;
}

.grid-3,
.feature-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.grid-4,
.profile-links-grid,
.interests-grid,
.awards-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.media-strip-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.research-practice-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.service-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
}

.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 1.35rem;
  padding: 1.5rem;
  box-shadow: var(--shadow);
}

.card h3,
.feature-title,
.case-title,
.publication-title,
.grant-title,
.service-title,
.award-name,
.mini-heading {
  margin: 0 0 0.45rem;
  font-size: 1.15rem;
  line-height: 1.25;
}

.card p,
.feature-desc,
.publication-text,
.grant-meta,
.service-body,
.award-meta,
.case-copy,
.mini-copy {
  margin: 0;
  color: var(--text2);
}

.feature-card,
.profile-link-card,
.interest-card,
.service-card,
.award-card,
.case-card,
.publication-card,
.grant-card,
.affiliation-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 1.35rem;
  box-shadow: var(--shadow);
  transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease;
}

.feature-card:hover,
.profile-link-card:hover,
.interest-card:hover,
.service-card:hover,
.award-card:hover,
.case-card:hover,
.publication-card:hover,
.grant-card:hover,
.affiliation-card:hover {
  transform: translateY(-3px);
  border-color: var(--border-strong);
  box-shadow: var(--shadow-strong);
}

.feature-card,
.profile-link-card,
.interest-card,
.service-card,
.award-card,
.grant-card,
.affiliation-card {
  padding: 1.45rem;
}

.service-card {
  min-width: 0;
}

.feature-card,
.profile-link-card {
  text-decoration: none;
}

.feature-kicker,
.card-kicker,
.publication-kicker,
.grant-status,
.service-kicker,
.case-kicker {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--navy);
}

.feature-kicker::before,
.card-kicker::before,
.publication-kicker::before,
.service-kicker::before,
.case-kicker::before {
  content: "";
  width: 1rem;
  height: 2px;
  background: currentColor;
}

.feature-title,
.strip-title {
  font-size: 1.25rem;
}

.feature-link,
.profile-link-arrow {
  display: inline-flex;
  margin-top: 1rem;
  color: var(--navy);
  font-weight: 700;
  font-size: 0.9rem;
}

.strip {
  margin: 0 -1.5rem;
  padding: 3rem 1.5rem;
  background: linear-gradient(135deg, #0a1e52, #173574 62%, #0f2d6b);
  color: white;
}

[data-theme="dark"] .strip {
  background: linear-gradient(135deg, #06152d, #0b2450 62%, #12336a);
}

.strip-inner {
  max-width: 1200px;
  margin: 0 auto;
}

.strip-heading {
  margin-bottom: 1.6rem;
}

.strip-heading p {
  margin: 0;
  max-width: 42rem;
  color: rgba(255, 255, 255, 0.78);
}

.strip-title {
  margin: 0 0 0.6rem;
}

.award-card {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.12);
  box-shadow: none;
}

.award-card:hover { border-color: rgba(255, 255, 255, 0.22); }

.award-name,
.award-meta {
  color: white;
}

.award-meta {
  color: rgba(255, 255, 255, 0.78);
  font-size: 0.93rem;
}

.publications-list,
.publication-sections,
.grants-list,
.affiliation-grid,
.case-list {
  display: grid;
  gap: 1.15rem;
}

.publication-card,
.grant-card {
  padding: 1.35rem 1.45rem;
}

.publication-card {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 1rem;
  align-items: start;
}

.publication-year {
  min-width: 4rem;
  font-size: 1.05rem;
  color: var(--navy);
}

.publication-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
  align-items: center;
  margin-bottom: 0.45rem;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 0.32rem 0.7rem;
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.status-published { background: rgba(22, 163, 74, 0.12); color: #166534; }
.status-accepted { background: rgba(37, 99, 235, 0.12); color: #1d4ed8; }
.status-review { background: rgba(202, 138, 4, 0.14); color: #854d0e; }

[data-theme="dark"] .status-published { background: rgba(74, 222, 128, 0.15); color: #86efac; }
[data-theme="dark"] .status-accepted { background: rgba(96, 165, 250, 0.16); color: #bfdbfe; }
[data-theme="dark"] .status-review { background: rgba(250, 204, 21, 0.15); color: #fde68a; }

.publication-section {
  padding: 1.6rem;
  border-radius: 1.45rem;
  background: var(--card);
  border: 1px solid var(--border);
  box-shadow: var(--shadow);
}

.publication-section h3 {
  margin: 0 0 1rem;
  font-family: 'Lora', serif;
  font-size: 1.45rem;
}

.publication-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 2rem;
  height: 2rem;
  border-radius: 999px;
  margin-left: 0.65rem;
  padding: 0 0.65rem;
  background: var(--navy);
  color: white;
  font-size: 0.8rem;
  font-weight: 800;
}

.publication-entry {
  padding: 1rem 0;
  border-top: 1px solid var(--border);
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.9rem;
}

.publication-entry:first-of-type { border-top: 0; padding-top: 0; }

.publication-index {
  min-width: 2.2rem;
  text-align: center;
  padding: 0.25rem 0.45rem;
  border-radius: 0.6rem;
  background: var(--navy-soft);
  color: var(--navy);
  font-size: 0.75rem;
  font-weight: 800;
}

.publication-copy {
  min-width: 0;
}

.publication-copy p {
  margin: 0;
  color: var(--text2);
}

.grant-grid {
  display: grid;
  gap: 1rem;
}

.grant-card {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 1rem;
}

.grant-title {
  font-size: 1.08rem;
}

.grant-meta {
  font-size: 0.92rem;
}

.grant-side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.45rem;
  text-align: right;
}

.grant-amount {
  font: 600 1.15rem 'Lora', serif;
  color: var(--navy);
}

.two-column {
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: 1.4rem;
}

.affiliation-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.affiliation-card {
  padding: 1.2rem;
  text-align: center;
}

.affiliation-name {
  margin: 0 0 0.35rem;
  font-size: 1rem;
  font-weight: 700;
}

.affiliation-note {
  margin: 0;
  color: var(--text3);
  font-size: 0.88rem;
}

.service-card h3,
.interest-card h3,
.profile-link-card h3 {
  margin-top: 0.7rem;
}

.service-body {
  font-size: 0.96rem;
  line-height: 1.7;
}

.profile-link-card {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.case-card {
  overflow: hidden;
}

.case-gallery {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  padding: 1rem 1rem 0;
}

.case-gallery .media-card img {
  aspect-ratio: 4 / 3;
  min-height: 0;
}

.case-header {
  background: linear-gradient(135deg, #0f2d6b, #1c4ba3);
  color: white;
  padding: 1.7rem;
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 1rem;
  align-items: start;
}

[data-theme="dark"] .case-header {
  background: linear-gradient(135deg, #0b1f45, #17418d);
}

.case-number {
  font: 600 2.6rem 'Lora', serif;
  color: rgba(255, 255, 255, 0.2);
  line-height: 1;
}

.case-kicker,
.case-title,
.case-subtitle,
.case-header .tag-list span {
  color: white;
}

.case-title {
  font-size: 1.55rem;
  margin: 0.25rem 0 0.55rem;
}

.case-subtitle {
  margin: 0;
  color: rgba(255, 255, 255, 0.78);
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.95rem;
}

.tag-list span {
  display: inline-flex;
  padding: 0.38rem 0.7rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.14);
  color: var(--navy);
  font-size: 0.78rem;
  font-weight: 700;
  border: 1px solid var(--border);
}

.case-header .tag-list span {
  border-color: rgba(255, 255, 255, 0.18);
}

.case-body {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.case-panel {
  padding: 1.5rem;
  border-top: 1px solid var(--border);
  border-right: 1px solid var(--border);
}

.case-panel:nth-child(2n) { border-right: 0; }

.case-panel h4,
.mini-heading {
  margin: 0 0 0.6rem;
  font-size: 0.82rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--navy);
}

.case-panel p,
.case-panel li,
.mini-copy {
  margin: 0;
  color: var(--text2);
}

.case-panel ul {
  margin: 0;
  padding-left: 1.05rem;
}

.case-panel li + li { margin-top: 0.35rem; }

.case-reflection {
  padding: 1.5rem;
  background: linear-gradient(180deg, rgba(15, 45, 107, 0.04), transparent);
  border-top: 1px solid var(--border);
}

.case-reflection p {
  margin: 0;
  color: var(--text2);
  font-style: italic;
}

.cta-card {
  display: grid;
  grid-template-columns: 1.1fr auto;
  gap: 1.4rem;
  align-items: center;
  padding: 1.65rem;
  border: 1px solid var(--border);
  border-radius: 1.5rem;
  background: linear-gradient(180deg, var(--card-strong), var(--card));
  box-shadow: var(--shadow);
}

.cta-card p,
.mini-block p,
.footer-tagline,
.footer-meta {
  margin: 0;
  color: var(--text2);
}

.mini-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.mini-block {
  padding: 1.2rem;
  border: 1px solid var(--border);
  border-radius: 1.15rem;
  background: var(--card);
  box-shadow: var(--shadow);
}

.site-footer {
  margin-top: 2rem;
  padding: 3rem 1.5rem 2rem;
  background: linear-gradient(135deg, #0a1e52, #173574 65%, #0f2d6b);
  color: white;
}

[data-theme="dark"] .site-footer {
  background: linear-gradient(135deg, #06152d, #0b2450 65%, #14356d);
}

.footer-inner {
  max-width: 1200px;
  margin: 0 auto;
}

.footer-grid {
  display: grid;
  grid-template-columns: 1.5fr 1fr 1fr 1fr;
  gap: 2rem;
}

.footer-brand {
  font-size: 1.2rem;
  margin: 0 0 0.55rem;
}

.footer-tagline,
.footer-meta,
.footer-col a {
  color: rgba(255, 255, 255, 0.78);
}

.footer-col h4 {
  margin: 0 0 0.95rem;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.56);
}

.footer-col a {
  display: block;
  text-decoration: none;
  margin-bottom: 0.55rem;
}

.footer-col a:hover { color: white; }

.footer-bottom {
  margin-top: 2rem;
  padding-top: 1.25rem;
  border-top: 1px solid rgba(255, 255, 255, 0.12);
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.fade {
  opacity: 0;
  transform: translateY(18px);
  transition: opacity 0.6s ease, transform 0.6s ease;
}

.fade.is-visible {
  opacity: 1;
  transform: none;
}

@media (max-width: 1060px) {
  .hero,
  .two-column,
  .cta-card,
  .footer-grid {
    grid-template-columns: 1fr;
  }

  .grid-4,
  .profile-links-grid,
  .interests-grid,
  .awards-grid,
  .affiliation-grid,
  .media-strip-grid,
  .case-gallery,
  .research-practice-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .metrics-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .metric-card:nth-child(3) { border-right: 0; }
}

@media (max-width: 860px) {
  .nav-links,
  .nav-actions .nav-cta,
  .nav-actions .theme-toggle {
    display: none;
  }

  .hamburger { display: inline-flex; }
  .hero { padding-top: 3.8rem; }
  .case-body,
  .mini-grid,
  .grant-card,
  .publication-card {
    grid-template-columns: 1fr;
  }

  .grant-side {
    align-items: flex-start;
    text-align: left;
  }
}

@media (max-width: 680px) {
  .main-wrap { padding: 0 1rem 4rem; }
  .metrics-band,
  .strip,
  .section-alt { margin-left: -1rem; margin-right: -1rem; }
  .grid-3,
  .feature-grid,
  .grid-4,
  .profile-links-grid,
  .interests-grid,
  .awards-grid,
  .affiliation-grid,
  .metrics-grid,
  .media-strip-grid,
  .case-gallery,
  .hero-visual-grid,
  .research-practice-grid {
    grid-template-columns: 1fr;
  }

  .metric-card {
    border-right: 0;
    border-bottom: 1px solid var(--border);
  }

  .metric-card:last-child { border-bottom: 0; }
  .page-hero { padding-top: 6.1rem; }
}
"""

SHARED_JS = """const root = document.documentElement;
const storageKey = 'da-portfolio-theme';
const particleCanvas = document.getElementById('particles');

function applyTheme(theme) {
  root.setAttribute('data-theme', theme);
  document.querySelectorAll('[data-theme-label]').forEach((node) => {
    node.textContent = theme === 'dark' ? 'Light' : 'Dark';
  });
}

const savedTheme = localStorage.getItem(storageKey) || 'light';
applyTheme(savedTheme);

document.querySelectorAll('[data-theme-toggle]').forEach((button) => {
  button.addEventListener('click', () => {
    const next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    localStorage.setItem(storageKey, next);
    applyTheme(next);
    initParticles();
  });
});

const mobileButton = document.querySelector('[data-mobile-toggle]');
const mobileNav = document.querySelector('[data-mobile-nav]');
if (mobileButton && mobileNav) {
  mobileButton.addEventListener('click', () => {
    const next = !mobileNav.classList.contains('is-open');
    mobileNav.classList.toggle('is-open', next);
    mobileButton.classList.toggle('is-open', next);
    mobileButton.setAttribute('aria-expanded', String(next));
  });

  mobileNav.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => {
      mobileNav.classList.remove('is-open');
      mobileButton.classList.remove('is-open');
      mobileButton.setAttribute('aria-expanded', 'false');
    });
  });
}

const fadeObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.classList.add('is-visible');
      fadeObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.12 });

document.querySelectorAll('.fade').forEach((node) => fadeObserver.observe(node));

const counterObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (!entry.isIntersecting) {
      return;
    }

    entry.target.querySelectorAll('[data-target]').forEach((node) => {
      const target = Number(node.getAttribute('data-target') || '0');
      const suffix = node.getAttribute('data-suffix') || '+';
      let current = 0;
      const step = Math.max(1, Math.ceil(target / 30));
      const timer = window.setInterval(() => {
        current = Math.min(target, current + step);
        node.textContent = `${current}${suffix}`;
        if (current >= target) {
          window.clearInterval(timer);
        }
      }, 35);
    });

    counterObserver.unobserve(entry.target);
  });
}, { threshold: 0.32 });

document.querySelectorAll('[data-counter-group]').forEach((node) => counterObserver.observe(node));

let particles = [];
let context = null;
let width = 0;
let height = 0;

function particlePalette() {
  return root.getAttribute('data-theme') === 'dark'
    ? ['#8bb4ff', '#b4ccff', '#f0c76a', '#ffffff']
    : ['#0f2d6b', '#1f4ba3', '#c3902f', '#6d8fd4'];
}

function resizeCanvas() {
  if (!particleCanvas) {
    return;
  }
  width = particleCanvas.width = window.innerWidth;
  height = particleCanvas.height = window.innerHeight;
}

function initParticles() {
  if (!particleCanvas) {
    return;
  }

  context = particleCanvas.getContext('2d');
  resizeCanvas();
  const colors = particlePalette();
  const count = Math.max(28, Math.floor((width * height) / 16000));
  particles = Array.from({ length: count }, () => ({
    x: Math.random() * width,
    y: Math.random() * height,
    radius: Math.random() * 1.8 + 0.6,
    color: colors[Math.floor(Math.random() * colors.length)],
    driftX: (Math.random() - 0.5) * 0.15,
    driftY: Math.random() * 0.22 + 0.05,
    alpha: Math.random() * 0.45 + 0.25,
    phase: Math.random() * Math.PI * 2,
  }));
}

function animateParticles() {
  if (!context || !particleCanvas) {
    return;
  }

  context.clearRect(0, 0, width, height);
  particles.forEach((particle) => {
    particle.y -= particle.driftY;
    particle.x += particle.driftX;
    particle.phase += 0.02;

    if (particle.y < -6) particle.y = height + 6;
    if (particle.x < -6) particle.x = width + 6;
    if (particle.x > width + 6) particle.x = -6;

    context.beginPath();
    context.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2);
    context.fillStyle = particle.color;
    context.globalAlpha = particle.alpha * (0.7 + 0.3 * Math.sin(particle.phase));
    context.fill();
  });
  context.globalAlpha = 1;
  window.requestAnimationFrame(animateParticles);
}

if (particleCanvas) {
  initParticles();
  animateParticles();
  window.addEventListener('resize', initParticles, { passive: true });
}
"""


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


def remove_reference_prefix(text: str) -> str:
    return re.sub(r"^\[\d+\]\s*", "", text).strip()


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
    return "Tuscaloosa, Alabama"


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


def truncate_text(text: str, limit: int = 220) -> str:
    cleaned = normalize_whitespace(text)
    if len(cleaned) <= limit:
        return cleaned
    shortened = cleaned[: limit - 3].rsplit(" ", 1)[0]
    return f"{shortened}..."


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
    if not text or text.endswith("."):
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
                "items": items,
            }
        )
        index += 2
    return skills


def parse_citation(citation: str, kind_label: str) -> dict[str, str]:
    cleaned = remove_reference_prefix(citation)
    status = citation_status(cleaned)[0]
    year = extract_year(cleaned)
    match = re.search(r"\)\.\s*(.+)", cleaned)
    title = cleaned
    context = kind_label
    if match:
        remainder = match.group(1).strip()
        pieces = [piece.strip() for piece in remainder.split(". ") if piece.strip()]
        if pieces:
            title = pieces[0].rstrip(".")
            if len(pieces) > 1:
                context = pieces[1].split("https://")[0].split("Manuscript")[0].strip().rstrip(".").rstrip("(").strip()
    return {
        "title": title,
        "context": context,
        "status": status,
        "year": year,
        "raw": cleaned,
    }


def citation_status(text: str) -> tuple[str, str]:
    lowered = text.lower()
    if any(token in lowered for token in ("accepted", "in press")):
        return "Accepted", "accepted"
    if any(token in lowered for token in ("under review", "submitted", "revision")):
        return "Under Review", "review"
    return "Published", "published"


def extract_year(text: str) -> str:
    match = re.search(r"\b(20\d{2}|19\d{2})\b", text)
    return match.group(1) if match else "Recent"


def summarize_grant(text: str) -> dict[str, str]:
    cleaned = remove_reference_prefix(text)
    title, remainder = (cleaned.split(". ", 1) + [""])[:2]
    lowered = cleaned.lower()
    if "[awarded]" in lowered or "funded" in lowered or "awarded" in lowered:
        status = "Funded"
    elif "nominee" in lowered:
        status = "Nominee"
    elif "applicant" in lowered or "applied" in lowered:
        status = "Applicant"
    elif "resubmission" in lowered:
        status = "Resubmission"
    else:
        status = "Grant or Fellowship"

    amount_match = re.search(r"\$[\d,]+", cleaned)
    return {
        "title": title.strip(),
        "context": remainder.strip() or "Grant or fellowship",
        "status": status,
        "amount": amount_match.group(0) if amount_match else "",
    }


def summarize_service_items(items: list[dict[str, str]], limit: int = 2) -> str:
    if not items:
        return ""
    names = [item["name"] for item in items[:limit]]
    summary = ", ".join(names)
    if len(items) > limit:
        summary = f"{summary}, and more."
    return truncate_text(summary, 130)


def is_showcase_role(entry: dict[str, Any]) -> bool:
    title = entry["title"].strip()
    if not title or title.endswith(".") or len(title) > 70:
        return False
    if title.lower().startswith(("research on ", "analysis of ", "collection, ")):
        return False
    return True


def years_of_experience(sections: dict[str, list[str]]) -> int:
    years = [int(match) for line in sections.values() for text in line for match in re.findall(r"\b(20\d{2}|19\d{2})\b", text)]
    if not years:
        return 1
    return max(1, date.today().year - min(years) + 1)


def build_affiliation_cards(raw_affiliations: list[dict[str, str]]) -> list[dict[str, str]]:
    cards: list[dict[str, str]] = []
    for item in raw_affiliations:
        name = item["name"]
        cards.append({"name": name, "note": AFFILIATION_DETAILS.get(name, "Professional affiliation")})
    return cards


def compact_name(full_name: str) -> str:
    parts = full_name.split()
    if len(parts) >= 2:
        return " ".join(parts[-2:])
    return full_name


def initials_from_name(name: str) -> str:
    parts = [part[0] for part in name.split() if part]
    return "".join(parts[:2]).upper() or "DA"


def build_site_data() -> dict[str, Any]:
    paragraphs = read_docx_paragraphs(SOURCE_DOCX)
    header, sections = split_sections(paragraphs)

    publications_grouped = group_subsections(sections.get("PUBLICATIONS", []), PUBLICATION_SUBHEADINGS)
    service_grouped = group_subsections(sections.get("PROFESSIONAL AND COMMUNITY SERVICE", []), SERVICE_SUBHEADINGS)

    journal_articles = [remove_reference_prefix(item) for item in list_items(publications_grouped.get("Peer-reviewed Journal Articles", []))]
    book_chapters = [remove_reference_prefix(item) for item in list_items(publications_grouped.get("Book Chapters", []))]
    proceedings = [remove_reference_prefix(item) for item in list_items(publications_grouped.get("Referred Conference Proceedings", []))]
    conference_presentations = [remove_reference_prefix(item) for item in list_items(sections.get("CONFERENCE PRESENTATIONS", []))]
    grants = [summarize_grant(line) for line in sections.get("GRANTS", [])]
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
    profile_summary = sections.get("PROFILE SUMMARY", [""])[0]

    stable_roles = [
        entry
        for entry in (research_entries + teaching_entries + design_entries)
        if "guest lecture" not in entry["title"].lower()
        and "workshop facilitator" not in entry["title"].lower()
        and is_showcase_role(entry)
    ]

    featured_roles = stable_roles[:4]
    selected_publications = [parse_citation(item, "Journal Article") for item in journal_articles[:4]]
    top_awards = awards[:6]
    funded_grants = [grant for grant in grants if grant["status"] == "Funded"]

    person_name = header[0] if header else "Idowu David Awoyemi"
    person = {
        "name": person_name,
        "display_name": compact_name(person_name),
        "initials": initials_from_name(person_name),
        "affiliation": header[1] if len(header) > 1 else "The University of Alabama",
        "location": infer_location(header),
        "email": email,
        "phone": phone,
        "phone_href": phone_href(phone),
        "expected_phd": "Spring 2027",
        "role": "Instructional Technology Researcher | AI and XR in Education | Learning Designer",
    }

    research_themes = [
        {
            "title": "Immersive Learning Systems",
            "body": "Designs and studies virtual and mixed reality environments for authentic STEM learning, safety training, and performance transfer.",
        },
        {
            "title": "AI-Enhanced Education",
            "body": "Explores generative AI, AI literacy, instructional decision-making, and responsible integration of emerging tools in learning environments.",
        },
        {
            "title": "Learning Analytics",
            "body": "Uses multimodal evidence, behavioral traces, and statistical reasoning to understand how learners engage and improve over time.",
        },
        {
            "title": "Equity and Participation",
            "body": "Advances broadening participation in STEM and computing through inclusive design, teacher development, and responsive learning pathways.",
        },
    ]

    publication_sections = [
        {"title": "Peer-Reviewed Journal Articles", "items": journal_articles},
        {"title": "Book Chapters", "items": book_chapters},
        {"title": "Refereed Conference Proceedings", "items": proceedings},
        {"title": "Conference Presentations", "items": conference_presentations},
    ]

    service_snapshot = [
        {
            "eyebrow": "Journal Reviewing",
            "title": f"{len(service_journals)} review appointments",
            "body": summarize_service_items(service_journals),
        },
        {
            "eyebrow": "Conference Service",
            "title": f"{len(service_chairs) + len(service_reviews)} conference roles",
            "body": summarize_service_items(service_chairs + service_reviews),
        },
        {
            "eyebrow": "Mentoring",
            "title": f"{len(service_mentoring)} mentoring engagements",
            "body": summarize_service_items(service_mentoring),
        },
        {
            "eyebrow": "Community Engagement",
            "title": f"{len(service_outreach)} outreach contributions",
            "body": summarize_service_items(service_outreach),
        },
    ]

    data = {
        "generated_on": date.today().isoformat(),
        "source_file": SOURCE_DOCX.name,
        "person": person,
        "profile_summary": profile_summary,
        "education": parse_education(sections.get("EDUCATION", [])),
        "profile_links": PROFILE_LINKS,
        "research_themes": research_themes,
        "metrics": [
            {"value": len(journal_articles), "label": "Journal Articles"},
            {"value": len(conference_presentations), "label": "Conference Presentations"},
            {"value": years_of_experience(sections), "label": "Years Experience"},
            {"value": len(awards), "label": "Awards and Scholarships"},
            {"value": len(funded_grants), "label": "Funded Projects"},
        ],
        "featured_roles": featured_roles,
        "selected_publications": selected_publications,
        "publication_sections": publication_sections,
        "grants": grants,
        "awards": awards,
        "certifications": certifications,
        "skills": skills,
        "primary_skill_tags": [item for skill in skills[:3] for item in skill["items"][:3]][:9],
        "leadership_cards": leadership_entries[:4],
        "affiliations": build_affiliation_cards(affiliations),
        "service_snapshot": service_snapshot,
        "journal_service": service_journals,
        "conference_service": service_chairs + service_reviews,
        "research_case_studies": RESEARCH_CASE_STUDIES,
    }
    return data


def escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


def link_attrs(url: str) -> str:
    return ' target="_blank" rel="noreferrer"' if url.startswith("http") else ""


def render_media_cards(items: list[dict[str, str]], extra_class: str = "") -> str:
    class_attr = f' class="media-card {extra_class}"' if extra_class else ' class="media-card"'
    return "\n".join(
        f"""
        <figure{class_attr}>
          <img src="{escape(item['src'])}" alt="{escape(item['alt'])}">
          {'<figcaption>' + escape(item['caption']) + '</figcaption>' if item.get('caption') else ''}
        </figure>
        """.rstrip()
        for item in items
    )


def render_nav(data: dict[str, Any], active: str) -> str:
    person = data["person"]
    links = [
        ("home", "Home", "index.html"),
        ("academic", "Academic Profile", "academic.html"),
        ("research", "Research Projects", "research.html"),
    ]
    links_html = "\n".join(
        f'<li><a href="{href}" class="{"is-active" if key == active else ""}">{label}</a></li>'
        for key, label, href in links
    )
    mobile_html = "\n".join(
        f'<a href="{href}" class="{"is-active" if key == active else ""}">{label}</a>'
        for key, label, href in links
    )
    return f"""
<header class="site-nav">
  <div class="nav-inner">
    <a class="brand" href="index.html">
      <span class="brand-mark">{escape(person["initials"])}</span>
      <span class="brand-text">
        <span class="brand-name">{escape(person["display_name"])}</span>
        <span class="brand-subtitle">Instructional Technology</span>
      </span>
    </a>
    <ul class="nav-links" aria-label="Primary navigation">
{links_html}
    </ul>
    <div class="nav-actions">
      <button class="theme-toggle" type="button" data-theme-toggle>
        <span data-theme-label>Dark</span>
      </button>
      <a class="nav-cta" href="{escape(data["source_file"])}">Download CV</a>
      <button class="hamburger" type="button" data-mobile-toggle aria-expanded="false" aria-label="Toggle menu">
        <span></span>
        <span></span>
        <span></span>
      </button>
    </div>
  </div>
  <div class="mobile-nav" data-mobile-nav>
    {mobile_html}
    <div class="mobile-nav-actions">
      <button class="mobile-theme-toggle" type="button" data-theme-toggle>
        <span data-theme-label>Dark</span>
      </button>
      <a class="button" href="{escape(data["source_file"])}">Download CV</a>
    </div>
  </div>
</header>
""".strip()


def render_footer(data: dict[str, Any]) -> str:
    person = data["person"]
    generated_label = date.fromisoformat(data["generated_on"]).strftime("%B %d, %Y")
    profile_links = "\n".join(
        f'<a href="{escape(item["url"])}"{link_attrs(item["url"])}>{escape(item["label"])}</a>'
        for item in data["profile_links"]
    )
    return f"""
<footer class="site-footer">
  <div class="footer-inner">
    <div class="footer-grid">
      <div class="footer-col">
        <h3 class="footer-brand">{escape(person["name"])}</h3>
        <p class="footer-tagline">{escape(person["role"])}</p>
        <p class="footer-meta">{escape(person["affiliation"])} · {escape(person["location"])}</p>
      </div>
      <div class="footer-col">
        <h4>Pages</h4>
        <a href="index.html">Home</a>
        <a href="academic.html">Academic Profile</a>
        <a href="research.html">Research Projects</a>
        <a href="{escape(data["source_file"])}">Download CV</a>
      </div>
      <div class="footer-col">
        <h4>Profiles</h4>
        {profile_links}
      </div>
      <div class="footer-col">
        <h4>Contact</h4>
        <a href="mailto:{escape(person["email"])}">{escape(person["email"])}</a>
        <a href="tel:{escape(person["phone_href"])}">{escape(person["phone"])}</a>
        <a href="mailto:{escape(person["email"])}?subject=Website%20Inquiry">Start a conversation</a>
      </div>
    </div>
    <div class="footer-bottom">
      <p>Generated from {escape(data["source_file"])} on {escape(generated_label)}</p>
      <p><a href="https://kinddave.github.io/david-awoyemi-academic-site/">GitHub Pages site</a></p>
    </div>
  </div>
</footer>
""".strip()


def render_page(title: str, description: str, active: str, body: str, data: dict[str, Any]) -> str:
    return f"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape(title)}</title>
  <meta name="description" content="{escape(description)}">
  <link rel="stylesheet" href="shared.css">
</head>
<body>
  <canvas id="particles" aria-hidden="true"></canvas>
  <div class="page-shell">
    {render_nav(data, active)}
    {body}
  </div>
  {render_footer(data)}
  <script src="shared.js"></script>
</body>
</html>
"""


def render_home(data: dict[str, Any]) -> str:
    person = data["person"]
    hero_highlights = "\n".join(f"<li>{escape(item['name'])}</li>" for item in data["awards"][:3])
    research_practice_media = render_media_cards(HOME_RESEARCH_PRACTICE)
    metrics = "\n".join(
        f"""
        <article class="metric-card">
          <span class="metric-value" data-target="{item['value']}" data-suffix="+">0+</span>
          <span class="metric-label">{escape(item['label'])}</span>
        </article>
        """.rstrip()
        for item in data["metrics"]
    )
    profile_links = "\n".join(
        f'<a class="pill-link" href="{escape(item["url"])}"{link_attrs(item["url"])}>{escape(item["label"])}</a>'
        for item in data["profile_links"][:3]
    )
    features = [
        ("Academic Profile", "CV-driven publications, presentations, grants, service, and affiliations.", "academic.html"),
        ("Research Projects", "Selected case studies showing how David designs, studies, and evaluates learning innovation.", "research.html"),
        ("Full CV and Contact", "Download the source-of-truth CV or start a conversation about roles, collaborations, and speaking.", data["source_file"]),
    ]
    features_html = "\n".join(
        f"""
        <a class="feature-card fade" href="{escape(href)}">
          <span class="feature-kicker">Portfolio Section</span>
          <h3 class="feature-title">{escape(title)}</h3>
          <p class="feature-desc">{escape(description)}</p>
          <span class="feature-link">Open section</span>
        </a>
        """.rstrip()
        for title, description, href in features
    )
    awards_html = "\n".join(
        f"""
        <article class="award-card fade">
          <h3 class="award-name">{escape(item['name'])}</h3>
          <p class="award-meta">{escape(item['date'] or 'Recognition')}</p>
        </article>
        """.rstrip()
        for item in data["awards"][:6]
    )
    publications_html = "\n".join(
        f"""
        <article class="publication-card fade">
          <div class="publication-year">{escape(item['year'])}</div>
          <div>
            <div class="publication-meta">
              <span class="status-badge status-{escape(citation_status(item['raw'])[1])}">{escape(item['status'])}</span>
            </div>
            <h3 class="publication-title">{escape(item['title'])}</h3>
            <p class="publication-text">{escape(item['context'])}</p>
          </div>
        </article>
        """.rstrip()
        for item in data["selected_publications"]
    )
    education_html = "\n".join(
        f"""
        <div class="mini-block fade">
          <h4 class="mini-heading">{escape(item['date'])}</h4>
          <p class="mini-copy"><strong>{escape(item['degree'])}</strong><br>{escape(item['institution'])}</p>
        </div>
        """.rstrip()
        for item in data["education"]
    )
    body = f"""
<main class="main-wrap">
  <section class="hero">
    <div class="hero-photo fade">
      <div class="profile-photo-card">
        <img src="{escape(HERO_HEADSHOT['src'])}" alt="{escape(HERO_HEADSHOT['alt'])}">
      </div>
      <div class="profile-links-inline">
        {profile_links}
      </div>
    </div>
    <div class="hero-copy fade">
      <span class="eyebrow">Ph.D. Candidate · University of Alabama</span>
      <h1>{escape(person["name"])}</h1>
      <div class="hero-role">{escape(person["role"])}</div>
      <p>{escape(data["profile_summary"])}</p>
      <p>David studies immersive learning, AI-supported instruction, analytics, and equitable participation in STEM with a design orientation grounded in practical educational impact.</p>
      <div class="hero-actions">
        <a class="button" href="academic.html">Explore my work</a>
        <a class="button-secondary" href="{escape(data["source_file"])}">View full CV</a>
        <a class="button-secondary" href="mailto:{escape(person["email"])}">Contact David</a>
      </div>
      <ul class="highlight-list">
        {hero_highlights}
      </ul>
    </div>
  </section>
</main>

<section class="metrics-band" data-counter-group>
  <div class="metrics-grid">
    {metrics}
  </div>
</section>

<main class="main-wrap">
  <section class="section">
    <div class="section-heading">
      <span class="eyebrow">Navigate the Portfolio</span>
      <h2>Start with the sections most useful for academic search, collaboration, and review.</h2>
      <p>This first automated multi-page version keeps the structure of the earlier handcrafted site while regenerating the core academic content from the Word CV.</p>
    </div>
    <div class="feature-grid">
      {features_html}
    </div>
  </section>

  <section class="section" style="padding-top: 0;">
    <div class="section-heading">
      <span class="eyebrow">Research in Practice</span>
      <h2>Project visuals moved under the work they represent.</h2>
      <p>These visuals now sit below the homepage introduction instead of competing with the headshot at the top of the page.</p>
    </div>
    <div class="media-strip-grid research-practice-grid">
      {research_practice_media}
    </div>
  </section>
</main>

<section class="strip">
  <div class="strip-inner">
    <div class="strip-heading">
      <span class="eyebrow" style="color: white;">Recent Recognition</span>
      <h2 class="strip-title">Awards, fellowships, and major acknowledgements.</h2>
      <p>These highlights are pulled from the current CV so the public-facing site and scholarly record stay aligned.</p>
    </div>
    <div class="awards-grid">
      {awards_html}
    </div>
  </div>
</section>

<main class="main-wrap">
  <section class="section">
    <div class="section-heading">
      <span class="eyebrow">Recent Scholarship</span>
      <h2>Selected outputs from the current publication record.</h2>
      <p>For the full list, including conference presentations and proceedings, use the academic profile page or download the source CV.</p>
    </div>
    <div class="publications-list">
      {publications_html}
    </div>
  </section>

  <section class="section-alt">
    <div class="section-inner">
      <div class="two-column">
        <div>
          <div class="section-heading">
            <span class="eyebrow">Education</span>
            <h2>Graduate training and academic formation.</h2>
            <p>Doctoral and prior degree work provide the foundation for current research and design practice.</p>
          </div>
          <div class="mini-grid">
            {education_html}
          </div>
        </div>
        <div>
          <div class="cta-card">
            <div>
              <span class="eyebrow">Workflow</span>
              <h3 class="feature-title">This site is regenerated from {escape(data["source_file"])}.</h3>
              <p>The Word CV is the source of truth. Updating the CV and running the local build refreshes these pages and the GitHub Pages deployment.</p>
            </div>
            <div class="hero-actions">
              <a class="button" href="research.html">View case studies</a>
              <a class="button-secondary" href="{escape(data["source_file"])}">Download CV</a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</main>
"""
    return render_page(
        f"{person['name']} | Instructional Technology Scholar",
        f"Academic portfolio for {person['name']}, generated from the current CV.",
        "home",
        body,
        data,
    )


def render_publication_sections(sections: list[dict[str, Any]]) -> str:
    section_html: list[str] = []
    for section in sections:
        entries = []
        for index, item in enumerate(section["items"], start=1):
            status_label, status_class = citation_status(item)
            year = extract_year(item)
            entries.append(
                f"""
                <div class="publication-entry">
                  <div class="publication-index">[{index}]</div>
                  <div class="publication-copy">
                    <div class="publication-meta">
                      <span class="publication-kicker">{escape(year)}</span>
                      <span class="status-badge status-{escape(status_class)}">{escape(status_label)}</span>
                    </div>
                    <p>{escape(item)}</p>
                  </div>
                </div>
                """.rstrip()
            )
        section_html.append(
            f"""
            <section class="publication-section fade">
              <h3>{escape(section['title'])}<span class="publication-count">{len(section['items'])}</span></h3>
              {''.join(entries) if entries else '<p class="publication-text">No entries available.</p>'}
            </section>
            """.rstrip()
        )
    return "\n".join(section_html)


def render_academic(data: dict[str, Any]) -> str:
    person = data["person"]
    academic_media = render_media_cards(ACADEMIC_MEDIA)
    profile_links = "\n".join(
        f"""
        <a class="profile-link-card fade" href="{escape(item['url'])}"{link_attrs(item["url"])}>
          <span class="card-kicker">Profile Link</span>
          <h3>{escape(item['label'])}</h3>
          <p>{escape(item['description'])}</p>
          <span class="profile-link-arrow">Open resource</span>
        </a>
        """.rstrip()
        for item in data["profile_links"]
    )
    interests = "\n".join(
        f"""
        <article class="interest-card fade">
          <span class="card-kicker">Research Interest</span>
          <h3>{escape(item['title'])}</h3>
          <p>{escape(item['body'])}</p>
        </article>
        """.rstrip()
        for item in data["research_themes"]
    )
    grants = "\n".join(
        f"""
        <article class="grant-card fade">
          <div>
            <div class="grant-status">{escape(item['status'])}</div>
            <h3 class="grant-title">{escape(item['title'])}</h3>
            <p class="grant-meta">{escape(item['context'])}</p>
          </div>
          <div class="grant-side">
            <div class="grant-amount">{escape(item['amount'] or 'Selected')}</div>
            <div class="grant-meta">{escape(item['status'])}</div>
          </div>
        </article>
        """.rstrip()
        for item in data["grants"]
    )
    affiliations = "\n".join(
        f"""
        <article class="affiliation-card fade">
          <h3 class="affiliation-name">{escape(item['name'])}</h3>
          <p class="affiliation-note">{escape(item['note'])}</p>
        </article>
        """.rstrip()
        for item in data["affiliations"]
    )
    journal_service = "\n".join(
        f"""
        <article class="service-card fade">
          <span class="service-kicker">Journal Service</span>
          <h3>{escape(item['name'])}</h3>
          <p class="service-body">{escape(item['date'] or 'Reviewer')}</p>
        </article>
        """.rstrip()
        for item in data["journal_service"][:6]
    )
    service_snapshot = "\n".join(
        f"""
        <article class="service-card fade">
          <span class="service-kicker">{escape(item['eyebrow'])}</span>
          <h3 class="service-title">{escape(item['title'])}</h3>
          <p class="service-body">{escape(item['body'])}</p>
        </article>
        """.rstrip()
        for item in data["service_snapshot"]
    )
    body = f"""
<main class="main-wrap">
  <section class="page-hero">
    <span class="eyebrow">Academic Profile</span>
    <h1>Research, publications, grants, and scholarly service.</h1>
    <p>This page formalizes the CV-backed academic record inside the stronger multi-page design system from the earlier website.</p>
  </section>

  <section class="section" style="padding-top: 0;">
    <div class="media-strip-grid">
      {academic_media}
    </div>
  </section>

  <section class="section">
    <div class="section-heading">
      <span class="eyebrow">Find Me Online</span>
      <h2>Key profiles and source documents.</h2>
      <p>Use these links for publications, lab affiliation, and the full downloadable CV.</p>
    </div>
    <div class="profile-links-grid">
      {profile_links}
    </div>
  </section>

  <section class="section-alt">
    <div class="section-inner">
      <div class="section-heading">
        <span class="eyebrow">Research Interests</span>
        <h2>Core strands shaping the scholarly agenda.</h2>
        <p>The themes below summarize the questions and design commitments that connect publications, funded projects, and collaborative work.</p>
      </div>
      <div class="interests-grid">
        {interests}
      </div>
    </div>
  </section>

  <section class="section">
    <div class="section-heading">
      <span class="eyebrow">Publications and Presentations</span>
      <h2>Structured directly from the Word CV.</h2>
      <p>Journal articles, book chapters, proceedings, and conference presentations are rebuilt each time the source CV is updated.</p>
    </div>
    <div class="publication-sections">
      {render_publication_sections(data["publication_sections"])}
    </div>
  </section>

  <section class="section-alt">
    <div class="section-inner two-column">
      <div>
        <div class="section-heading">
          <span class="eyebrow">Grants and Fellowships</span>
          <h2>Funded initiatives and competitive applications.</h2>
          <p>These entries are surfaced from the grants section of the CV and presented as a quick reviewable list.</p>
        </div>
        <div class="grant-grid">
          {grants}
        </div>
      </div>
      <div>
        <div class="section-heading">
          <span class="eyebrow">Service Snapshot</span>
          <h2>Reviewing, mentoring, and community contribution.</h2>
          <p>Scholarly service work complements the publication record and reflects ongoing participation in the field.</p>
        </div>
        <div class="service-grid">
          {service_snapshot}
        </div>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="section-heading">
      <span class="eyebrow">Affiliations</span>
      <h2>Professional memberships and editorial presence.</h2>
      <p>Memberships, review work, and conference roles show the broader academic community surrounding the research agenda.</p>
    </div>
    <div class="two-column">
      <div>
        <div class="affiliation-grid">
          {affiliations}
        </div>
      </div>
      <div>
        <div class="service-grid">
          {journal_service}
        </div>
      </div>
    </div>
  </section>
</main>
"""
    return render_page(
        f"Academic Profile | {person['name']}",
        f"Academic profile for {person['name']} including publications, grants, and service.",
        "academic",
        body,
        data,
    )


def render_case_studies(cases: list[dict[str, Any]]) -> str:
    html_blocks: list[str] = []
    for case in cases:
        stakeholders = "".join(f"<li>{escape(item)}</li>" for item in case["stakeholders"])
        frameworks = "".join(f"<li>{escape(item)}</li>" for item in case["frameworks"])
        methods = "".join(f"<li>{escape(item)}</li>" for item in case["methods"])
        outcomes = "".join(f"<li>{escape(item)}</li>" for item in case["outcomes"])
        tags = "".join(f"<span>{escape(item)}</span>" for item in case["tags"])
        gallery = render_media_cards(
            [{"src": item["src"], "alt": item["alt"], "caption": ""} for item in case.get("images", [])],
            extra_class="gallery-card",
        )
        html_blocks.append(
            f"""
            <article class="case-card fade">
              <div class="case-header">
                <div class="case-number">{escape(case['number'])}</div>
                <div>
                  <span class="case-kicker">{escape(case['label'])}</span>
                  <h3 class="case-title">{escape(case['title'])}</h3>
                  <p class="case-subtitle">{escape(case['subtitle'])}</p>
                  <div class="tag-list">{tags}</div>
                </div>
              </div>
              <div class="case-gallery">
                {gallery}
              </div>
              <div class="case-body">
                <div class="case-panel">
                  <h4>Problem Context</h4>
                  <p>{escape(case['problem'])}</p>
                </div>
                <div class="case-panel">
                  <h4>Stakeholders and Context</h4>
                  <ul>{stakeholders}</ul>
                </div>
                <div class="case-panel">
                  <h4>Frameworks</h4>
                  <ul>{frameworks}</ul>
                </div>
                <div class="case-panel">
                  <h4>Methods and Tools</h4>
                  <ul>{methods}</ul>
                </div>
                <div class="case-panel" style="grid-column: 1 / -1;">
                  <h4>Design Contribution</h4>
                  <p>{escape(case['solution'])}</p>
                </div>
                <div class="case-panel" style="grid-column: 1 / -1;">
                  <h4>Outcomes</h4>
                  <ul>{outcomes}</ul>
                </div>
              </div>
              <div class="case-reflection">
                <h4>Critical Reflection</h4>
                <p>{escape(case['reflection'])}</p>
              </div>
            </article>
            """.rstrip()
        )
    return "\n".join(html_blocks)


def render_research(data: dict[str, Any]) -> str:
    person = data["person"]
    role_cards = "\n".join(
        f"""
        <article class="mini-block fade">
          <h4 class="mini-heading">{escape(item['date'])}</h4>
          <p class="mini-copy"><strong>{escape(item['title'])}</strong><br>{escape(item['organization'] or item['summary'])}</p>
        </article>
        """.rstrip()
        for item in data["featured_roles"]
    )
    theme_tags = "".join(f"<span>{escape(item['title'])}</span>" for item in data["research_themes"])
    body = f"""
<main class="main-wrap">
  <section class="page-hero">
    <span class="eyebrow">Research Projects</span>
    <h1>Evidence-based learning innovation across XR, AI, and analytics.</h1>
    <p>This page keeps the stronger case-study structure from the earlier website while connecting it to the same shared automated workflow.</p>
  </section>

  <section class="section">
    <div class="two-column">
      <div>
        <div class="section-heading">
          <span class="eyebrow">Research Agenda</span>
          <h2>Project work organized as case-based evidence.</h2>
          <p>These studies show how David approaches design, evaluation, and scholarly contribution across immersive learning, AI literacy, and multimodal analytics.</p>
        </div>
        <div class="tag-list">{theme_tags}</div>
      </div>
      <div>
        <div class="section-heading">
          <span class="eyebrow">Core Roles</span>
          <h2>Appointments that shaped the project portfolio.</h2>
          <p>These roles come directly from the CV and provide context for the design and research work described below.</p>
        </div>
        <div class="mini-grid">
          {role_cards}
        </div>
      </div>
    </div>
  </section>

  <section class="section-alt">
    <div class="section-inner">
      <div class="section-heading">
        <span class="eyebrow">Selected Case Studies</span>
        <h2>Three projects that best represent the research story.</h2>
        <p>The content below preserves the narrative richness of the previous site while using the new shared design system and deploy workflow.</p>
      </div>
      <div class="case-list">
        {render_case_studies(data["research_case_studies"])}
      </div>
    </div>
  </section>

  <section class="section">
    <div class="cta-card">
      <div>
        <span class="eyebrow">Next Layer</span>
        <h3 class="feature-title">Research case studies now live inside the automated site.</h3>
        <p>The case narratives remain curated, while the linked academic record on the profile page continues to regenerate from the Word CV.</p>
      </div>
      <div class="hero-actions">
        <a class="button" href="academic.html">View academic profile</a>
        <a class="button-secondary" href="{escape(data["source_file"])}">Download CV</a>
      </div>
    </div>
  </section>
</main>
"""
    return render_page(
        f"Research Projects | {person['name']}",
        f"Selected research projects for {person['name']} across XR, AI, and learning analytics.",
        "research",
        body,
        data,
    )


def write_outputs(data: dict[str, Any]) -> None:
    pages = {
        "index.html": render_home(data),
        "academic.html": render_academic(data),
        "research.html": render_research(data),
    }

    OUTPUT_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    ROOT_SHARED_CSS.write_text(SHARED_CSS, encoding="utf-8")
    ROOT_SHARED_JS.write_text(SHARED_JS, encoding="utf-8")
    ROOT_STYLES.write_text("/* Compatibility wrapper: shared styles now live in shared.css. */\n@import url('./shared.css');\n", encoding="utf-8")

    for filename, content in pages.items():
        (ROOT / filename).write_text(content, encoding="utf-8")

    DIST_DIR.mkdir(exist_ok=True)

    for filename, content in pages.items():
        (DIST_DIR / filename).write_text(content, encoding="utf-8")

    (DIST_DIR / OUTPUT_JSON.name).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    (DIST_DIR / ROOT_SHARED_CSS.name).write_text(SHARED_CSS, encoding="utf-8")
    (DIST_DIR / ROOT_SHARED_JS.name).write_text(SHARED_JS, encoding="utf-8")
    (DIST_DIR / ROOT_STYLES.name).write_text(ROOT_STYLES.read_text(encoding="utf-8"), encoding="utf-8")
    if ASSET_DIR.exists():
        shutil.copytree(ASSET_DIR, DIST_ASSET_DIR, dirs_exist_ok=True)
    shutil.copy2(SOURCE_DOCX, DIST_DIR / SOURCE_DOCX.name)
    NOJEKYLL.write_text("", encoding="utf-8")


def main() -> None:
    data = build_site_data()
    write_outputs(data)
    print("Built multi-page website from CV_David.docx into root HTML files and dist/.")


if __name__ == "__main__":
    main()
