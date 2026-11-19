"""Configuration module for Internship JARVIS.

Defines the candidate's profile, matching criteria, and environment settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the repository
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env if present
load_dotenv(BASE_DIR / ".env")

# ==========================================
# CANDIDATE PROFILE CONFIGURATION
# ==========================================
CANDIDATE_PROFILE = {
    "name": "Candidate",
    "education": "B.Tech Computer Science & Engineering",
    "college": "Jabalpur Engineering College",
    "start_year": 2025,
    "graduation_year": 2029,
    "current_semester": 3,
    "year_of_study": 2,  # 2nd year student
    # Projected graduation batch for 4-year degree starting 2025
    "target_grad_years": [2028, 2029],
    # Primary skills in candidate's toolkit
    "skills": [
        "python",
        "c",
        "sql",
        "html",
        "css",
        "javascript",
        "git",
    ],
    # Areas of interest
    "interests": [
        "software development",
        "software engineering",
        "ai",
        "artificial intelligence",
        "ml",
        "machine learning",
        "data science",
        "technology research",
        "research",
    ],
    # Positive target signals for early undergraduate students (2028/2029 batch)
    "early_student_signals": [
        "intern",
        "internship",
        "trainee",
        "apprentice",
        "fellowship",
        "undergraduate",
        "bachelor",
        "freshman",
        "sophomore",
        "college",
        "student",
        "early career",
        "entry level",
        "entry-level",
        "2028",
        "2029",
        "summer 2025",
        "summer 2026",
    ],
    # Negative signals / exclusions (roles requiring extensive experience)
    "exclusion_keywords": [
        "senior",
        "lead",
        "principal",
        "staff",
        "director",
        "head of",
        "vp",
        "manager",
        "5+ years",
        "6+ years",
        "7+ years",
        "8+ years",
        "10+ years",
    ],
}

# Known in-demand tech skills to monitor for "missing skills" gap analysis
EXPANDED_SKILL_LEXICON = [
    "c++",
    "java",
    "golang",
    "rust",
    "typescript",
    "react",
    "next.js",
    "node.js",
    "express",
    "django",
    "flask",
    "fastapi",
    "docker",
    "kubernetes",
    "aws",
    "gcp",
    "azure",
    "linux",
    "mongodb",
    "postgresql",
    "mysql",
    "redis",
    "pytorch",
    "tensorflow",
    "pandas",
    "numpy",
    "scikit-learn",
    "graphql",
    "rest api",
    "ci/cd",
    "opencv",
    "nlp",
]

# ==========================================
# SYSTEM & ENVIRONMENT CONFIGURATION
# ==========================================
GMAIL_USER = (os.getenv("GMAIL_ADDRESS") or os.getenv("GMAIL_USER") or "").strip()
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "").strip()
RECIPIENT_EMAIL = (os.getenv("RECIPIENT_EMAIL") or GMAIL_USER).strip()
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "https://internship-jarvis.onrender.com/").strip()

# If credentials are missing, automatically fall back to DRY_RUN mode so local runs succeed
DRY_RUN = os.getenv("DRY_RUN", "").lower() in ("true", "1", "yes") or not (GMAIL_USER and GMAIL_APP_PASSWORD)

# Match scoring thresholds
MIN_MATCH_SCORE = int(os.getenv("MIN_MATCH_SCORE", "40"))
MAX_RESULTS_PER_SECTION = int(os.getenv("MAX_RESULTS_PER_SECTION", "30"))

# Storage paths
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
SEEN_JOBS_FILE = DATA_DIR / "seen_jobs.json"
LATEST_MATCHES_FILE = DATA_DIR / "latest_matches.json"
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)
