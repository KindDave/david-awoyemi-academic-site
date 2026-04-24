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

HOME_RESEARCH_PRACTICE: list[dict[str, str]] = []

ACADEMIC_MEDIA = [
    {
        "src": "assets/images/headshot-stage.jpg",
        "alt": "David Awoyemi presenting at a conference podium",
        "caption": "Conference and scholarly presentation",
    },
    {
        "src": "assets/images/conference-1.jpeg",
        "alt": "David Awoyemi at a research conference presentation",
        "caption": "Conference participation and presentation",
    },
    {
        "src": "assets/images/conference-2.jpeg",
        "alt": "David Awoyemi during an academic conference event",
        "caption": "Academic conference engagement",
    },
    {
        "src": "assets/images/conference-3.jpeg",
        "alt": "David Awoyemi at a conference venue",
        "caption": "Scholarly networking and dissemination",
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
        "images": [],
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
        "images": [],
    },
]

ABOUT_BIO = [
    "I am Idowu David Awoyemi, a Ph.D. candidate in Instructional Technology at the University of Alabama whose work bridges learning sciences, instructional design, and emerging technologies for more equitable educational experiences.",
    "Across research, teaching, and design practice, I build learning environments that are analytically rigorous, human-centered, and responsive to the realities of learners, instructors, and institutions.",
    "My scholarly identity sits at the intersection of AI-supported learning, immersive environments, multimodal analytics, and the design of technology-mediated instruction that improves both access and performance.",
]

ABOUT_HIGHLIGHTS = [
    "Most Outstanding Graduate Student in Research (2025)",
    "Alabama Power Innovation and Technology Award (2025)",
    "Instructional technology researcher with practice across higher education, K-12, and faculty development",
    "Designs learning systems that connect research evidence with real implementation contexts",
]

TEACHING_FOUNDATION = [
    "I approach teaching as an act of intentional design. Every course, lesson, and interaction becomes an opportunity to create the conditions under which diverse learners can build understanding, develop agency, and apply knowledge in authentic settings.",
    "Doctoral training and instructional practice helped me move from technology integration as a tool choice toward a fuller view of teaching as evidence-based orchestration of cognition, motivation, and participation.",
    "That philosophy now shapes how I scaffold learning, interpret data, offer feedback, and select technology only when it genuinely improves access, clarity, engagement, or transfer.",
]

TEACHING_FRAMEWORKS = [
    {
        "icon": "UDL",
        "title": "Universal Design for Learning",
        "body": "Builds multiple means of engagement, representation, and expression into instruction so learner variability is expected rather than treated as an exception.",
    },
    {
        "icon": "TPACK",
        "title": "TPACK Framework",
        "body": "Positions technology decisions inside the relationship among pedagogy, disciplinary content, and the realities of a teaching context.",
    },
    {
        "icon": "CLT",
        "title": "Constructivism and Cognitive Apprenticeship",
        "body": "Supports active sensemaking, modeling, guided practice, and collaborative knowledge building around meaningful problems.",
    },
    {
        "icon": "LXD",
        "title": "Backward Design and ADDIE",
        "body": "Starts with learning outcomes and assessment evidence, then structures instruction systematically to make those outcomes achievable.",
    },
    {
        "icon": "CRT",
        "title": "Culturally Responsive Teaching",
        "body": "Centers identity, relevance, and belonging so learners can connect disciplinary work to their own experiences and futures.",
    },
    {
        "icon": "L.A.",
        "title": "Learning Analytics and Feedback",
        "body": "Uses formative evidence, interaction data, and reflective assessment to improve instruction while learning is still happening.",
    },
]

TEACHING_ACCORDION = [
    {
        "title": "Introduction: My Journey as an Educator",
        "subtitle": "From mathematics instruction in Nigeria to doctoral teaching and design work in the United States.",
        "paragraphs": [
            "My teaching philosophy emerged through practice across multiple institutional and cultural settings. I began by teaching mathematics in Nigeria, where I learned quickly that engagement rises when instruction feels meaningful, active, and connected to learners' realities.",
            "Doctoral study in instructional technology gave me conceptual language for instincts I had already developed: learning is designed, participation is structured, and good teaching is iterative, reflective, and evidence-informed.",
        ],
    },
    {
        "title": "Designing for Learner Variability",
        "subtitle": "Why access, flexibility, and support are core design decisions rather than accommodations added later.",
        "paragraphs": [
            "I teach with the assumption that learners differ in prior knowledge, confidence, pace, digital access, and preferred ways of demonstrating understanding.",
            "That belief leads me to design with choice, multimodal materials, scaffolded tasks, and feedback loops so students can enter learning productively and keep moving forward.",
        ],
    },
    {
        "title": "The Role of the Teacher",
        "subtitle": "Teacher as facilitator, designer, and reflective researcher of learning in context.",
        "paragraphs": [
            "I see the teacher as more than a presenter of content. The teacher is a designer of environments, a facilitator of inquiry, and a professional who studies how learners respond to the conditions that have been created.",
            "That stance matters especially in technology-rich contexts, where novelty can distract from learning unless design choices stay anchored to outcomes, evidence, and care for the learner experience.",
        ],
    },
    {
        "title": "Technology, Equity, and Reflection",
        "subtitle": "How I decide when technology belongs in a course and how I evaluate whether it helped.",
        "paragraphs": [
            "I do not treat technology as an end in itself. I use it when it makes learning more accessible, more authentic, more collaborative, or more analyzable in ways that improve teaching and learning.",
            "Reflection is essential to that process. After every teaching cycle, I look for evidence about where students struggled, where engagement dropped, and where design revisions can better support equity and transfer.",
        ],
    },
]

CONTACT_POSITIONS = [
    "Assistant Professor — Instructional Technology",
    "Assistant Professor — Educational Technology",
    "Senior Instructional Designer — Higher Education",
    "Learning Experience Designer — University or College",
    "Post-Doctoral Research Fellow",
    "Research Scientist — EdTech",
]

CONTACT_PROFILES = [
    {"label": "Google Scholar", "url": "https://scholar.google.com/citations?user=NIWz8s4AAAAJ&hl=en", "desc": "Publications and citations"},
    {"label": "ResearchGate", "url": "https://www.researchgate.net/profile/Idowu-Awoyemi-2", "desc": "Research network"},
    {"label": "ADIE Lab", "url": "https://sites.ua.edu/adielab/people/", "desc": "Lab profile"},
    {"label": "Teaching Dossier", "url": "https://sites.google.com/view/david-teaching-dossier/home", "desc": "Teaching record"},
    {"label": "Adobe Portfolio", "url": "https://idawoyemi.myportfolio.com/work", "desc": "Design work"},
    {"label": "Exam Portfolio", "url": "https://portfolios.davidawoyemi.net/", "desc": "Doctoral portfolio"},
]

PORTFOLIO_FEATURED = {
    "title": "Articulate Rise 360 Interactive Tutorial",
    "subtitle": "A polished, self-paced multimedia lesson on two-dimensional geometric shapes built for learner autonomy, clarity, and accessibility.",
    "body": "This project demonstrates how I design interactive instruction with narrative pacing, embedded media, learner choice, and accessibility-aware structure. It remains one of the clearest examples of my instructional development process from storyboard to polished experience.",
    "tags": ["Articulate Rise 360", "Interactive Multimedia", "Accessibility", "Elementary Mathematics"],
    "links": [
        {"label": "Launch Interactive Module", "url": "https://360.articulate.com/review/content/d5649f65-923e-4144-906c-409b7eb97ddd/review"},
        {"label": "Read Portfolio Reflection", "url": "https://portfolios.davidawoyemi.net/ail605/"},
    ],
}

PORTFOLIO_CURRICULUM_MEDIA = [
    {
        "src": "assets/images/portfolio-camp-characters.jpg",
        "alt": "Story characters for the Code, Sensors, and Me summer camp curriculum",
        "caption": "Narrative characters used to anchor learner engagement in the camp curriculum.",
    },
    {
        "src": "assets/images/portfolio-camp-roadmap.jpg",
        "alt": "Roadmap of 16 activities in the Code, Sensors, and Me curriculum",
        "caption": "A sequenced roadmap linking physiological computing, coding, and design challenges.",
    },
    {
        "src": "assets/images/portfolio-camp-team.jpg",
        "alt": "Research team photo for the NSF ITEST summer camp project",
        "caption": "The interdisciplinary research and implementation team behind the project.",
    },
    {
        "src": "assets/images/portfolio-camp-schedule.jpg",
        "alt": "Weekly camp schedule for the Code, Sensors, and Me project",
        "caption": "Daily planning that coordinated coding, sensing, reflection, and facilitation.",
    },
]

PORTFOLIO_TRAINING_MEDIA = [
    {
        "src": "assets/images/portfolio-training-cit.jpg",
        "alt": "Workshop cover for a faculty development session",
        "caption": "Faculty development documentation for Hypothesis annotation in Blackboard.",
    },
    {
        "src": "assets/images/portfolio-training-boris.jpg",
        "alt": "BORIS workshop slide overview",
        "caption": "Behavioral observation and microgenetic analysis training for researchers.",
    },
    {
        "src": "assets/images/portfolio-training-onboarding.jpg",
        "alt": "Onboarding module slide for OTIDE training",
        "caption": "A learner-facing onboarding module designed through SME collaboration.",
    },
]

PORTFOLIO_COURSES = [
    {
        "code": "AIL-601",
        "term": "Foundations of Instructional Technology",
        "title": "Adobe Express Portfolio and UDL Reflection",
        "body": "Developed a portfolio demonstrating UDL, motivational theory, and core instructional technology concepts while clarifying my scholarly stance.",
        "links": [
            {"label": "View Adobe Express Portfolio", "url": "https://new.express.adobe.com/webpage/tHKB8XD6Vcq3I"},
            {"label": "Read Reflection", "url": "https://portfolios.davidawoyemi.net/ail-601/"},
        ],
    },
    {
        "code": "AIL-602",
        "term": "Instructional Design",
        "title": "Gagne Planning Sheet and Design Mapping",
        "body": "Applied systematic design models, including Gagne and TEC-VARIETY, to the sequencing and support structures that later informed immersive learning work.",
        "links": [
            {"label": "View Planning Artifact", "url": "https://drive.google.com/file/d/141afmW3n3ODqbwg9Nch7N5TNIG6BcY5y/view?usp=sharing"},
            {"label": "Read Reflection", "url": "https://portfolios.davidawoyemi.net/ail-602/"},
        ],
    },
    {
        "code": "AIL-604",
        "term": "Distance Learning Technologies",
        "title": "Canvas Course Prototype and Distance Learning Design",
        "body": "Designed online learning experiences with backward design, UDL, multimedia learning principles, and stronger attention to learner decision points.",
        "links": [
            {"label": "View Artifact", "url": "https://drive.google.com/file/d/1ONmk6bU7Pws5tdXsuwHx244y9V1aQLId/view?usp=sharing"},
            {"label": "Read Reflection", "url": "https://portfolios.davidawoyemi.net/ail-604/"},
        ],
    },
    {
        "code": "AIL-608",
        "term": "Emerging Technologies in Education",
        "title": "VR Hazard Identification Research Reflection",
        "body": "Connected XR design, AI-supported feedback, and research dissemination through a doctoral course that directly fed into the immersive safety training project.",
        "links": [
            {"label": "Vanguard Feature", "url": "https://www.vanguardngr.com/2023/08/expert-idowu-awoyemi-leads-team-in-revolutionizing-civil-engineering-education-with-vrt/"},
            {"label": "Read Reflection", "url": "https://portfolios.davidawoyemi.net/ail-608/"},
        ],
    },
    {
        "code": "AIL-605",
        "term": "Interactive Multimedia Processes",
        "title": "Rise 360 Interactive Tutorial and Reflection",
        "body": "Built a full interactive multimedia lesson with branching menus, audio narration, embedded videos, and accessibility-aware design choices.",
        "links": [
            {"label": "Launch Interactive Module", "url": "https://360.articulate.com/review/content/d5649f65-923e-4144-906c-409b7eb97ddd/review"},
            {"label": "Read Reflection", "url": "https://portfolios.davidawoyemi.net/ail605/"},
        ],
    },
    {
        "code": "AIL-689/690",
        "term": "Doctoral Seminar and Dissertation",
        "title": "Dissertation Prospectus and Program Reflection",
        "body": "Capstone documents showing research readiness, scholarly identity, and synthesis across the doctoral program in instructional technology.",
        "links": [
            {"label": "Read Prospectus", "url": "https://portfolios.davidawoyemi.net/prospectus/"},
            {"label": "Read Program Reflection", "url": "https://portfolios.davidawoyemi.net/ail601/"},
        ],
    },
]

PORTFOLIO_MORE_LINKS = [
    {"label": "Adobe Portfolio", "url": "https://idawoyemi.myportfolio.com/work"},
    {"label": "Teaching Dossier", "url": "https://sites.google.com/view/david-teaching-dossier/home"},
    {"label": "Exam Portfolio", "url": "https://portfolios.davidawoyemi.net/"},
    {"label": "Download Full CV", "url": SOURCE_DOCX.name},
]

PORTFOLIO_CURRICULUM_TABS = [
    {
        "id": "overview",
        "label": "Overview and Characters",
        "items": [
            {"src": "assets/images/portfolio-camp-characters.jpg", "alt": "Story characters for the camp curriculum", "caption": "Story characters: Zada, Milo, and Zappy the AI robot."},
            {"src": "assets/images/portfolio-camp-roadmap.jpg", "alt": "Roadmap of 16 activities", "caption": "Roadmap of 16 curriculum activities across coding, data, and sensing."},
        ],
    },
    {
        "id": "pd",
        "label": "Teacher PD",
        "items": [
            {"src": "assets/images/portfolio-camp-team.jpg", "alt": "Research team photo", "caption": "Research team and project leads."},
            {"src": "assets/images/portfolio-camp-agenda.jpg", "alt": "Two-day professional development agenda", "caption": "Two-day professional development agenda for teachers and facilitators."},
            {"src": "assets/images/portfolio-camp-schedule.jpg", "alt": "Weekly camp schedule", "caption": "Weekly schedule coordinating camp activities and data collection."},
        ],
    },
    {
        "id": "a1",
        "label": "Activities 1 to 5",
        "items": [
            {"src": "assets/images/portfolio-camp-activity-1.jpg", "alt": "Paper computer activity", "caption": "Paper computer activity introducing hardware and software logic."},
            {"src": "assets/images/portfolio-camp-activity-4.jpg", "alt": "Physiological data activity", "caption": "Learners using body-based data to connect sensing and computation."},
            {"src": "assets/images/portfolio-camp-activity-5.jpg", "alt": "Plotting heart rate data", "caption": "Students graphing heart rate data across activities."},
        ],
    },
    {
        "id": "a2",
        "label": "Activities 6 to 10",
        "items": [
            {"src": "assets/images/portfolio-camp-activity-6.jpg", "alt": "Energy hunt paper block programming", "caption": "Paper block programming for algorithmic thinking."},
            {"src": "assets/images/portfolio-camp-activity-8.jpg", "alt": "Simon says conditionals activity", "caption": "Conditionals and logic through kinesthetic gameplay."},
            {"src": "assets/images/portfolio-camp-activity-10.jpg", "alt": "Algorithm design activity", "caption": "Students creating pseudocode algorithms for daily tasks."},
        ],
    },
    {
        "id": "a3",
        "label": "Activities 11 to 16",
        "items": [
            {"src": "assets/images/portfolio-camp-activity-11.jpg", "alt": "Muscle energy coding activity", "caption": "Coding and sensing challenges in later-stage activities."},
            {"src": "assets/images/portfolio-camp-activity-14.jpg", "alt": "Banana piano Makey Makey activity", "caption": "Makey Makey circuitry and playful interaction design."},
            {"src": "assets/images/portfolio-camp-activity-16.jpg", "alt": "Coding lab with VEX AIM robot and EMG sensors", "caption": "Advanced coding lab with robotics and physiological sensors."},
        ],
    },
]

PORTFOLIO_VIDEO_TABS = [
    {
        "id": "music",
        "label": "Music (4 videos)",
        "items": [
            {
                "video_id": "lnE1iTkWluk",
                "title": "Introduction — Music Lesson One",
                "desc": "Introductory video for the arts-integrated music PD series, setting learning aims and the music-technology integration approach.",
                "tags": ["Arts Integration", "Music"],
            },
            {
                "video_id": "vKrdyFokmfM",
                "title": "Music Lesson Four",
                "desc": "Later-stage music module focused on classroom application and teacher professional development.",
                "tags": ["Arts Integration", "Music", "Teacher PD"],
            },
            {
                "video_id": "ZwEb9ss9b9A",
                "title": "The Symphony of Digital Skills",
                "desc": "A creative instructional video using musical metaphor to communicate digital competency frameworks for educators.",
                "tags": ["Digital Skills", "Creative Production"],
            },
            {
                "video_id": "hcGQv8W0gIQ",
                "title": "SOUNDRAW — AI Music Composition",
                "desc": "Demonstrates AI-supported music generation as a tool for creative instructional production.",
                "tags": ["AI Tools", "Music"],
            },
        ],
    },
    {
        "id": "theatre",
        "label": "Theatre (5 videos)",
        "items": [
            {
                "video_id": "nPbOreBLyWg",
                "title": "Welcome — Theatre Module",
                "desc": "Opening orientation for the theatre arts integration professional development sequence.",
                "tags": ["Theatre", "Arts Integration", "Teacher PD"],
            },
            {
                "video_id": "5OCrpv2Q_8I",
                "title": "Theatre Lesson Two — Digital Drama",
                "desc": "Builds deeper pedagogical strategy and classroom application into the theatre sequence.",
                "tags": ["Theatre", "Arts Integration"],
            },
            {
                "video_id": "UBwpV88g1bA",
                "title": "Theatre Lesson Three — Digital Storytelling",
                "desc": "Focuses on digital storytelling and formative assessment within arts-based instruction.",
                "tags": ["Theatre", "Formative Assessment"],
            },
            {
                "video_id": "ipQlIj_1kUY",
                "title": "Theatre Lesson Four",
                "desc": "Capstone lesson emphasizing performance-based assessment and reflective practice.",
                "tags": ["Theatre", "Summative Assessment"],
            },
            {
                "video_id": "9viWDW7cj1Q",
                "title": "Theatre Module — Full Overview",
                "desc": "Comprehensive overview of the full theatre module from introduction to evaluation.",
                "tags": ["Theatre", "Module Overview"],
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
        "research_entries": research_entries,
        "teaching_entries": teaching_entries,
        "design_entries": design_entries,
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
        ("about", "About", "about.html"),
        ("academic", "Academic Profile", "academic.html"),
        ("research", "Research Projects", "research.html"),
        ("teaching", "Teaching Philosophy", "teaching.html"),
        ("portfolio", "ID Portfolio", "portfolio.html"),
        ("contact", "Contact", "contact.html"),
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
      <a class="nav-cta" href="contact.html">Contact Me</a>
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
      <a class="button" href="contact.html">Contact Me</a>
      <a class="button-secondary" href="{escape(data["source_file"])}">Download CV</a>
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
        <a href="about.html">About</a>
        <a href="academic.html">Academic Profile</a>
        <a href="research.html">Research Projects</a>
        <a href="teaching.html">Teaching Philosophy</a>
        <a href="portfolio.html">ID Portfolio</a>
        <a href="contact.html">Contact</a>
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
        ("About", "Professional biography, training background, and a clearer view of the scholarly and design profile.", "about.html"),
        ("Academic Profile", "CV-driven publications, presentations, grants, service, and affiliations.", "academic.html"),
        ("Research Projects", "Selected case studies showing how David designs, studies, and evaluates learning innovation.", "research.html"),
        ("Teaching Philosophy", "Research-informed teaching commitments, frameworks, and experience across instructional contexts.", "teaching.html"),
        ("ID Portfolio", "Instructional design artifacts, curriculum work, multimedia development, and doctoral coursework.", "portfolio.html"),
        ("Contact and CV", "Open positions, professional contact details, and the source-of-truth academic CV.", "contact.html"),
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
    academic_media_section = f"""
  <section class="section" style="padding-top: 0;">
    <div class="media-strip-grid">
      {academic_media}
    </div>
  </section>
""" if academic_media else ""
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
  </section>

  {academic_media_section}

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
        gallery_section = f"""
              <div class="case-gallery">
                {gallery}
              </div>
""" if gallery else ""
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
              {gallery_section}
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


def render_about(data: dict[str, Any]) -> str:
    person = data["person"]
    highlights = "\n".join(f"<li>{escape(item)}</li>" for item in ABOUT_HIGHLIGHTS)
    bio = "\n".join(f"<p>{escape(item)}</p>" for item in ABOUT_BIO)
    education_html = "\n".join(
        f"""
        <article class="timeline-card fade">
          <div class="timeline-date">{escape(item['date'])}</div>
          <div>
            <h3 class="timeline-title">{escape(item['degree'])}</h3>
            <p class="timeline-org">{escape(item['institution'])}</p>
          </div>
        </article>
        """.rstrip()
        for item in data["education"]
    )
    skill_groups = "\n".join(
        f"""
        <article class="skill-cluster fade">
          <h3>{escape(skill['category'])}</h3>
          <div class="tag-cloud">
            {''.join(f'<span>{escape(item)}</span>' for item in skill['items'][:8])}
          </div>
        </article>
        """.rstrip()
        for skill in data["skills"][:6]
    )
    body = f"""
<main class="main-wrap">
  <section class="page-hero">
    <span class="eyebrow">About Me</span>
    <h1>Educator, researcher, and design-minded scholar.</h1>
    <p>This page restores the fuller personal and professional framing from the original site while keeping the broader website inside the new shared system.</p>
  </section>

  <section class="section">
    <div class="about-hero-grid">
      <div class="about-photo-stack fade">
        <div class="profile-photo-card">
          <img src="assets/images/headshot-linkedin.png" alt="Portrait of {escape(person['name'])}">
        </div>
      </div>
      <div class="about-copy fade">
        <span class="eyebrow">Who I Am</span>
        <h2>Scholarship grounded in design, evidence, and educational impact.</h2>
        {bio}
        <ul class="highlight-list compact-highlight-list">
          {highlights}
        </ul>
        <div class="hero-actions">
          <a class="button" href="academic.html">View academic profile</a>
          <a class="button-secondary" href="contact.html">Get in touch</a>
        </div>
      </div>
    </div>
  </section>

  <section class="section-alt">
    <div class="section-inner">
      <div class="section-heading">
        <span class="eyebrow">Education and Training</span>
        <h2>Graduate preparation and scholarly formation.</h2>
        <p>The educational timeline below draws directly from the CV and keeps degree history in sync with the broader academic profile.</p>
      </div>
      <div class="timeline-grid">
        {education_html}
      </div>
    </div>
  </section>

  <section class="section">
    <div class="section-heading">
      <span class="eyebrow">Skills and Tools</span>
      <h2>Research, design, and instructional technology capabilities.</h2>
      <p>These groupings are built from the technical and professional skills section of the source CV, then organized into cleaner clusters for easier scanning.</p>
    </div>
    <div class="skill-cluster-grid">
      {skill_groups}
    </div>
  </section>
</main>
"""
    return render_page(
        f"About | {person['name']}",
        f"About {person['name']}, including background, education, and skills.",
        "about",
        body,
        data,
    )


def render_teaching(data: dict[str, Any]) -> str:
    person = data["person"]
    foundations = "\n".join(f"<p>{escape(item)}</p>" for item in TEACHING_FOUNDATION)
    frameworks = "\n".join(
        f"""
        <article class="framework-card fade">
          <div class="framework-icon">{escape(item['icon'])}</div>
          <h3>{escape(item['title'])}</h3>
          <p>{escape(item['body'])}</p>
        </article>
        """.rstrip()
        for item in TEACHING_FRAMEWORKS
    )
    teaching_experience = "\n".join(
        f"""
        <article class="timeline-card fade">
          <div class="timeline-date">{escape(item['date'])}</div>
          <div>
            <h3 class="timeline-title">{escape(item['title'])}</h3>
            <p class="timeline-org">{escape(item['organization'] or item['summary'])}</p>
            <p class="timeline-copy">{escape(truncate_text(item['summary'], 180))}</p>
          </div>
        </article>
        """.rstrip()
        for item in data["teaching_entries"][:6]
    )
    certifications = "\n".join(
        f"""
        <article class="cert-card fade">
          <h3>{escape(item['name'])}</h3>
          <p>{escape(item['date'])}</p>
        </article>
        """.rstrip()
        for item in data["certifications"][:8]
    )
    accordion = "\n".join(
        f"""
        <article class="accordion-item fade">
          <button class="accordion-trigger" type="button" data-accordion-button aria-expanded="false">
            <span>
              <strong>{escape(item['title'])}</strong>
              <small>{escape(item['subtitle'])}</small>
            </span>
            <span class="accordion-plus">+</span>
          </button>
          <div class="accordion-panel" data-accordion-panel hidden>
            {''.join(f'<p>{escape(paragraph)}</p>' for paragraph in item['paragraphs'])}
          </div>
        </article>
        """.rstrip()
        for item in TEACHING_ACCORDION
    )
    body = f"""
<main class="main-wrap">
  <section class="page-hero">
    <span class="eyebrow">Teaching Philosophy</span>
    <h1>Learning-sciences-grounded teaching practice.</h1>
    <p>This page restores the fuller teaching narrative from the original website with a cleaner, more aligned presentation and mobile-friendly structure.</p>
  </section>

  <section class="section">
    <div class="about-hero-grid">
      <div class="about-photo-stack fade">
        <div class="profile-photo-card">
          <img src="assets/images/headshot-secondary.png" alt="{escape(person['name'])} in a professional portrait">
        </div>
      </div>
      <div class="about-copy fade">
        <span class="eyebrow">Teaching as Design</span>
        <h2>Intentional, evidence-informed, and learner-centered.</h2>
        {foundations}
        <div class="hero-actions">
          <a class="button" href="contact.html">Discuss teaching collaborations</a>
          <a class="button-secondary" href="portfolio.html">See design artifacts</a>
        </div>
      </div>
    </div>
  </section>

  <section class="section-alt">
    <div class="section-inner">
      <div class="section-heading">
        <span class="eyebrow">Frameworks That Guide My Practice</span>
        <h2>Theoretical commitments translated into teaching decisions.</h2>
        <p>These pillars shape how I design activities, structure support, evaluate learning, and decide when technology meaningfully belongs in the instructional environment.</p>
      </div>
      <div class="framework-grid">
        {frameworks}
      </div>
      <div class="quote-banner fade">
        <p>"I see teaching not as content transmission but as the design of conditions in which every learner can engage authentically, develop competence, and grow in agency."</p>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="section-heading">
      <span class="eyebrow">Teaching Philosophy In Depth</span>
      <h2>A fuller narrative for committees and collaborators.</h2>
      <p>The sections below preserve the intent of the original long-form teaching statement while making it easier to navigate.</p>
    </div>
    <div class="accordion-stack">
      {accordion}
    </div>
  </section>

  <section class="section-alt">
    <div class="section-inner two-column">
      <div>
        <div class="section-heading">
          <span class="eyebrow">Teaching Experience</span>
          <h2>Roles that shaped my instructional perspective.</h2>
          <p>These entries come directly from the CV and show how teaching practice developed across different responsibilities and contexts.</p>
        </div>
        <div class="timeline-grid">
          {teaching_experience}
        </div>
      </div>
      <div>
        <div class="section-heading">
          <span class="eyebrow">Certifications and Training</span>
          <h2>Continuing professional development.</h2>
          <p>Recent training supports my work in instructional design, AI, multimedia development, and course quality improvement.</p>
        </div>
        <div class="cert-grid-pro">
          {certifications}
        </div>
      </div>
    </div>
  </section>
</main>
"""
    return render_page(
        f"Teaching Philosophy | {person['name']}",
        f"Teaching philosophy, frameworks, and experience for {person['name']}.",
        "teaching",
        body,
        data,
    )


def render_tag_group(tags: list[str], class_name: str = "tag-list") -> str:
    return f'<div class="{class_name}">{"".join(f"<span>{escape(tag)}</span>" for tag in tags)}</div>'


def render_portfolio_video_card(item: dict[str, Any]) -> str:
    thumb = f"https://img.youtube.com/vi/{item['video_id']}/hqdefault.jpg"
    embed = f"https://www.youtube.com/embed/{item['video_id']}?autoplay=1&rel=0&modestbranding=1"
    return f"""
    <article class="video-card fade">
      <button class="video-thumb" type="button" data-play-video="{escape(embed)}" aria-label="Play {escape(item['title'])}">
        <img src="{escape(thumb)}" alt="{escape(item['title'])}">
        <span class="video-play">▶</span>
      </button>
      <div class="video-card-body">
        {render_tag_group(item['tags'], 'video-tag-list')}
        <h4>{escape(item['title'])}</h4>
        <p>{escape(item['desc'])}</p>
      </div>
    </article>
    """.rstrip()


def render_portfolio(data: dict[str, Any]) -> str:
    person = data["person"]

    featured_links = "".join(
        f'<a class="button{"-secondary" if index else ""}" href="{escape(link["url"])}"{link_attrs(link["url"])}>{escape(link["label"])}</a>'
        for index, link in enumerate(PORTFOLIO_FEATURED["links"])
    )

    curriculum_radios = "\n".join(
        f'<input type="radio" id="curr-{escape(item["id"])}" name="curriculum-tabs" class="tab-radio" {"checked" if index == 0 else ""}>'
        for index, item in enumerate(PORTFOLIO_CURRICULUM_TABS)
    )
    curriculum_labels = "\n".join(
        f'<label class="tab-label" for="curr-{escape(item["id"])}">{escape(item["label"])}</label>'
        for item in PORTFOLIO_CURRICULUM_TABS
    )
    curriculum_panels = "\n".join(
        f"""
        <div class="tab-panel curr-panel-{escape(item['id'])}">
          <div class="portfolio-gallery-grid portfolio-gallery-grid-wide">
            {render_media_cards(item['items'])}
          </div>
        </div>
        """.rstrip()
        for item in PORTFOLIO_CURRICULUM_TABS
    )

    video_radios = "\n".join(
        f'<input type="radio" id="video-{escape(item["id"])}" name="video-tabs" class="tab-radio" {"checked" if index == 0 else ""}>'
        for index, item in enumerate(PORTFOLIO_VIDEO_TABS)
    )
    video_labels = "\n".join(
        f'<label class="tab-label" for="video-{escape(item["id"])}">{escape(item["label"])}</label>'
        for item in PORTFOLIO_VIDEO_TABS
    )
    video_panels = "\n".join(
        f"""
        <div class="tab-panel video-panel-{escape(group['id'])}">
          <div class="video-grid">
            {"".join(render_portfolio_video_card(item) for item in group['items'])}
          </div>
        </div>
        """.rstrip()
        for group in PORTFOLIO_VIDEO_TABS
    )

    project_cards = "\n".join(
        f"""
        <article class="project-mini-card fade">
          <div class="project-mini-head">
            <span class="project-code">{escape(item['code'])}</span>
            <h3>{escape(item['title'])}</h3>
          </div>
          <p>{escape(item['body'])}</p>
          <div class="portfolio-links">
            {''.join(f'<a href="{escape(link["url"])}"{link_attrs(link["url"])}>{escape(link["label"])}</a>' for link in item['links'][:1])}
          </div>
        </article>
        """.rstrip()
        for item in PORTFOLIO_COURSES
    )

    course_tabs = "\n".join(
        f'<button class="course-tab{" is-active" if index == 0 else ""}" type="button" data-course-tab="{escape("all" if index == 0 else item["code"])}">{escape("All Projects" if index == 0 else item["code"])}</button>'
        for index, item in enumerate([{"code": "all"}] + PORTFOLIO_COURSES)
    )

    course_all = f"""
    <div class="course-panel is-active" data-course-panel="all">
      <div class="project-mini-grid">
        {project_cards}
      </div>
    </div>
    """.rstrip()

    course_panels = [course_all]
    for item in PORTFOLIO_COURSES:
        course_panels.append(
            f"""
            <div class="course-panel" data-course-panel="{escape(item['code'])}">
              <article class="course-detail-card fade">
                <div class="course-detail-head">
                  <div class="course-detail-code">{escape(item['code'])}</div>
                  <div>
                    <div class="course-detail-term">{escape(item['term'])}</div>
                    <h3>{escape(item['title'])}</h3>
                  </div>
                </div>
                <p class="course-detail-copy">{escape(item['body'])}</p>
                <div class="portfolio-links">
                  {''.join(f'<a href="{escape(link["url"])}"{link_attrs(link["url"])}>{escape(link["label"])}</a>' for link in item['links'])}
                </div>
              </article>
            </div>
            """.rstrip()
        )

    more_links = "\n".join(
        f'<a class="resource-link fade" href="{escape(item["url"])}"{link_attrs(item["url"])}>{escape(item["label"])}</a>'
        for item in PORTFOLIO_MORE_LINKS
    )

    body = f"""
<main class="main-wrap">
  <section class="page-hero">
    <span class="eyebrow">Instructional Design Portfolio</span>
    <h1>Design, development, and innovation.</h1>
    <p>A curated collection of instructional design artifacts, eLearning modules, multimedia projects, and doctoral course reflections demonstrating applied mastery across the instructional design cycle.</p>
  </section>

  <section class="section-alt">
    <div class="section-inner">
      <div class="section-heading">
        <span class="eyebrow">Featured Project</span>
        <h2>Articulate Rise 360 interactive tutorial.</h2>
        <p>Two-Dimensional Geometrical Shapes is a fully interactive, self-paced eLearning module using Rise 360 with branching menus, audio narration, embedded videos, and responsive design aligned with WCAG accessibility guidelines.</p>
      </div>
      <a href="{escape(PORTFOLIO_FEATURED['links'][0]['url'])}" class="featured-preview-card fade"{link_attrs(PORTFOLIO_FEATURED['links'][0]['url'])}>
        <div class="fpc-header">
          <span class="feh-badge">Articulate Rise 360</span>
          <span class="feh-badge feh-badge-alt">Click to Launch</span>
        </div>
        <div class="fpc-thumb">
          <img src="https://portfolios.davidawoyemi.net/wp-content/uploads/2025/05/Rise-360-AIL-605-1024x391.png" alt="Rise 360 tutorial preview">
          <div class="fpc-overlay">
            <div class="fpc-play">▶</div>
            <div class="fpc-play-text">Launch Interactive Module</div>
          </div>
        </div>
        <div class="fpc-footer">
          <div class="fpc-title">Interactive Tutorial: Two-Dimensional Geometrical Shapes</div>
          <div class="fpc-sub">AIL-605 · Interactive Multimedia Processes · Opens in new tab</div>
        </div>
      </a>
      <div class="hero-actions" style="margin-top: 1.2rem;">{featured_links}</div>
      {render_tag_group(PORTFOLIO_FEATURED['tags'], 'portfolio-skill-tags')}
    </div>
  </section>

  <section class="section-alt">
    <div class="section-inner">
      <div class="section-heading">
        <span class="eyebrow">AI-IVR Research Project</span>
        <h2>AI-immersive virtual reality intervention for civil engineering education.</h2>
        <p>Design and Development Research applying systematic instructional design methodology to an immersive VR-based safety training intervention with two learning phases and AI-driven adaptive feedback.</p>
      </div>
      <article class="ivr-feature-card fade">
        <div class="ivr-media-grid">
          <figure class="ivr-media ivr-media-main">
            <img src="assets/images/research-case1-1.jpeg" alt="VR construction safety training environment">
            <figcaption>SOS Construction scene</figcaption>
          </figure>
          <figure class="ivr-media">
            <img src="assets/images/research-case1-2.jpeg" alt="VR night scaffold hazard markers">
            <figcaption>Unstable scaffold</figcaption>
          </figure>
          <figure class="ivr-media">
            <img src="assets/images/research-case1-3.jpeg" alt="AI avatar inside VR training environment">
            <figcaption>AI avatar feedback</figcaption>
          </figure>
        </div>
        <div class="ivr-copy">
          <h3>Designing and developing an immersive virtual reality intervention for civil engineering education.</h3>
          <p>Phase 1 guides learners through hazard-identification scenarios. Phase 2 introduces an AI avatar that delivers diagnostic and corrective feedback. The work is grounded in experiential and situated learning theory and has already supported research dissemination across major venues.</p>
          <div class="ivr-metrics">
            <div><strong>Phase 1</strong><span>Hazard navigation across multiple scenarios</span></div>
            <div><strong>Phase 2</strong><span>AI avatar feedback and mastery-gated support</span></div>
          </div>
          {render_tag_group(["IVR and XR Design", "AI Avatar", "OSHA Training", "AERA 2026"], 'portfolio-skill-tags')}
          <div class="hero-actions">
            <a class="button" href="research.html">View Full Research</a>
          </div>
        </div>
      </article>
    </div>
  </section>

  <section class="section-alt">
    <div class="section-inner">
      <div class="section-heading">
        <span class="eyebrow">Curriculum Design and STEM Education</span>
        <h2>Code, Sensors, and Me — summer camp curriculum.</h2>
        <p>A 16-activity STEM curriculum for upper-elementary learners integrating physiological computing, visual coding, and culturally responsive STEM pedagogy, alongside a two-day teacher professional development sequence.</p>
      </div>
      {curriculum_radios}
      <div class="tab-bar">{curriculum_labels}</div>
      <div class="tab-panels">
        {curriculum_panels}
      </div>
    </div>
  </section>

  <section class="section">
    <div class="section-heading">
      <span class="eyebrow">Professional Development and Training Documentation</span>
      <h2>Workshop design, onboarding, and facilitation artifacts.</h2>
      <p>Training materials developed through SME collaboration, faculty development work, and eLearning design practice.</p>
    </div>
    <div class="portfolio-gallery-grid">
      {render_media_cards(PORTFOLIO_TRAINING_MEDIA)}
    </div>
  </section>

  <section class="section-alt">
    <div class="section-inner">
      <div class="section-heading">
        <span class="eyebrow">Arts and Technology PD Video Series</span>
        <h2>Music and theatre branches.</h2>
        <p>This section restores the original branching structure by separating the arts-integrated professional development videos into music and theatre tracks.</p>
      </div>
      {video_radios}
      <div class="tab-bar">{video_labels}</div>
      <div class="tab-panels">
        {video_panels}
      </div>
    </div>
  </section>

  <section class="section">
    <div class="section-heading">
      <span class="eyebrow">Doctoral Coursework Portfolio</span>
      <h2>Course artifacts and reflections.</h2>
      <p>Select a course to explore artifacts, reflections, and key learnings from the doctoral program in instructional technology.</p>
    </div>
    <div class="course-tabs">{course_tabs}</div>
    {"".join(course_panels)}
  </section>

  <section class="section-alt">
    <div class="section-inner">
      <div class="section-heading">
        <span class="eyebrow">Additional Resources</span>
        <h2>More of my work.</h2>
        <p>These links connect to the broader teaching, design, and doctoral portfolio ecosystem around this site.</p>
      </div>
      <div class="resource-link-grid">
        {more_links}
      </div>
    </div>
  </section>
</main>
"""
    return render_page(
        f"ID Portfolio | {person['name']}",
        f"Instructional design portfolio and learning artifacts for {person['name']}.",
        "portfolio",
        body,
        data,
    )


def render_contact(data: dict[str, Any]) -> str:
    person = data["person"]
    positions = "".join(f'<span class="position-pill">{escape(item)}</span>' for item in CONTACT_POSITIONS)
    contact_profiles = "\n".join(
        f"""
        <a class="profile-link-card fade" href="{escape(item['url'])}"{link_attrs(item["url"])}>
          <span class="card-kicker">Online Profile</span>
          <h3>{escape(item['label'])}</h3>
          <p>{escape(item['desc'])}</p>
          <span class="profile-link-arrow">Open resource</span>
        </a>
        """.rstrip()
        for item in CONTACT_PROFILES
    )
    body = f"""
<main class="main-wrap">
  <section class="page-hero">
    <span class="eyebrow">Contact and CV</span>
    <h1>Let's connect.</h1>
    <p>I am actively open to faculty, postdoctoral, research, and senior instructional design opportunities, as well as collaborations around AI, XR, and learning design.</p>
  </section>

  <section class="section">
    <div class="section-heading">
      <span class="eyebrow">Open to These Positions</span>
      <h2>Current opportunities and collaboration interests.</h2>
      <p>This keeps the practical contact framing from the original site while aligning the layout with the rest of the automated portfolio.</p>
    </div>
    <div class="position-pills">
      {positions}
    </div>
  </section>

  <section class="section-alt">
    <div class="section-inner contact-grid-pro">
      <div>
        <div class="section-heading">
          <span class="eyebrow">Get In Touch</span>
          <h2>Professional contact details and quick links.</h2>
          <p>I usually respond to professional inquiries within two business days. For academic roles, including the institution or search name in the subject line helps me respond faster.</p>
        </div>
        <div class="contact-detail-list">
          <article class="contact-detail-card fade">
            <h3>Email</h3>
            <p><a href="mailto:{escape(person['email'])}">{escape(person['email'])}</a></p>
          </article>
          <article class="contact-detail-card fade">
            <h3>Phone</h3>
            <p><a href="tel:{escape(person['phone_href'])}">{escape(person['phone'])}</a></p>
          </article>
          <article class="contact-detail-card fade">
            <h3>Office and Department</h3>
            <p>324 Autherine Lucy Hall · Box 870302<br>Tuscaloosa, AL 35487<br>ELPTS Department · University of Alabama</p>
          </article>
          <article class="contact-detail-card fade">
            <h3>Research Lab</h3>
            <p><a href="https://sites.ua.edu/adielab/people/" target="_blank" rel="noreferrer">ADIE Lab — University of Alabama</a></p>
          </article>
        </div>
      </div>
      <div>
        <div class="contact-form-card fade">
          <span class="eyebrow">Contact Form</span>
          <h2>Draft an email in one step.</h2>
          <p>This static form builds a ready-to-send email message so the site works cleanly on GitHub Pages without requiring a separate backend.</p>
          <form class="contact-form" data-mailto-form data-mailto-target="{escape(person['email'])}">
            <div class="form-row">
              <label>
                First name
                <input type="text" name="first_name" required>
              </label>
              <label>
                Last name
                <input type="text" name="last_name" required>
              </label>
            </div>
            <label>
              Email address
              <input type="email" name="reply_email" required>
            </label>
            <label>
              Institution or organization
              <input type="text" name="organization">
            </label>
            <label>
              Inquiry type
              <select name="inquiry_type">
                <option value="">Select inquiry type</option>
                <option>Faculty Position</option>
                <option>Instructional Design Position</option>
                <option>Research Collaboration</option>
                <option>Speaking or Guest Lecture</option>
                <option>Mentorship</option>
                <option>Other</option>
              </select>
            </label>
            <label>
              Subject
              <input type="text" name="subject" placeholder="Assistant Professor Position — Department of Educational Technology">
            </label>
            <label>
              Message
              <textarea name="message" rows="6" required placeholder="Please share details about your opportunity, institution, or inquiry."></textarea>
            </label>
            <button class="button" type="submit">Open email draft</button>
          </form>
        </div>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="section-heading">
      <span class="eyebrow">Online Profiles</span>
      <h2>Scholarly and professional web presence.</h2>
      <p>These links connect the CV-backed website to publication records, lab affiliation, teaching materials, and design portfolios.</p>
    </div>
    <div class="profile-links-grid">
      {contact_profiles}
    </div>
  </section>
</main>
"""
    return render_page(
        f"Contact | {person['name']}",
        f"Contact page for {person['name']} with professional details and opportunity interests.",
        "contact",
        body,
        data,
    )


def write_outputs(data: dict[str, Any]) -> None:
    pages = {
        "index.html": render_home(data),
        "about.html": render_about(data),
        "academic.html": render_academic(data),
        "research.html": render_research(data),
        "teaching.html": render_teaching(data),
        "portfolio.html": render_portfolio(data),
        "contact.html": render_contact(data),
    }

    OUTPUT_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    ROOT_STYLES.write_text("/* Compatibility wrapper: shared styles now live in shared.css. */\n@import url('./shared.css');\n", encoding="utf-8")

    for filename, content in pages.items():
        (ROOT / filename).write_text(content, encoding="utf-8")

    DIST_DIR.mkdir(exist_ok=True)

    for filename, content in pages.items():
        (DIST_DIR / filename).write_text(content, encoding="utf-8")

    (DIST_DIR / OUTPUT_JSON.name).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    shutil.copy2(ROOT_SHARED_CSS, DIST_DIR / ROOT_SHARED_CSS.name)
    shutil.copy2(ROOT_SHARED_JS, DIST_DIR / ROOT_SHARED_JS.name)
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
