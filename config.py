"""
AI Job Agent - Configuration
Edit this file to personalize your job search.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
# JOB SEARCH SETTINGS
# ─────────────────────────────────────────────
_raw_queries = os.getenv(
    "JOB_SEARCH_QUERIES",
    "Python Django Developer,Python Backend Engineer,Django REST Framework Developer,"
    "FastAPI Backend Developer,Senior Python Developer"
)
_raw_sites = os.getenv("JOB_SITES", "linkedin,indeed,zip_recruiter")

JOB_SEARCH_QUERIES        = [q.strip() for q in _raw_queries.split(",") if q.strip()]
JOB_SITES                 = [s.strip() for s in _raw_sites.split(",")   if s.strip()]
JOB_MAX_RESULTS_PER_QUERY = int(os.getenv("JOB_MAX_RESULTS_PER_QUERY", "5"))
JOB_HOURS_OLD             = int(os.getenv("JOB_HOURS_OLD", "24"))
# Note: remote filtering is handled per-site in scraper.py
# LinkedIn/ZipRecruiter → is_remote=True
# Indeed               → "remote" keyword appended to query + country_indeed="usa"

# Hard filters — jobs matching ANY of these keywords are discarded automatically
JOB_EXCLUDE_KEYWORDS = [
    # Work authorisation blockers
    "US citizen", "US Citizen", "U.S. citizen", "security clearance",
    "clearance required", "must be authorized to work",
    "authorized to work in the US", "authorized to work in the U.S",
    "sponsorship not available", "no sponsorship",
    # Seniority mismatches
    "junior", "Junior", "entry level", "Entry Level", "entry-level",
    "intern", "Intern", "internship",
    # On-site blockers
    "on-site only", "onsite only", "must be local", "in-office required",
    "no remote", "not remote",
]

# ─────────────────────────────────────────────
# RESUME SETTINGS
# ─────────────────────────────────────────────
RESUME_PDF_PATH = os.getenv("RESUME_PDF_PATH", "resume.pdf")  # Path to your PDF resume
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "tailored_resumes")       # Where DOCX outputs are saved

# ─────────────────────────────────────────────
# OPENAI SETTINGS
# ─────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# ─────────────────────────────────────────────
# EMAIL SETTINGS (Gmail)
# ─────────────────────────────────────────────
EMAIL_SENDER = os.getenv("EMAIL_SENDER", "")          # Your Gmail address
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")      # Gmail App Password (not your login password)
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT", "")    # Where to send the daily digest
EMAIL_SMTP_HOST = os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com")
EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", "587"))

# ─────────────────────────────────────────────
# SCHEDULER SETTINGS
# ─────────────────────────────────────────────
SCHEDULE_HOUR = int(os.getenv("SCHEDULE_HOUR", "7"))    # Run at 7 AM
SCHEDULE_MINUTE = int(os.getenv("SCHEDULE_MINUTE", "0"))
