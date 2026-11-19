"""Internship Matcher module.

Calculates match scores, analyzes skill matches and skill gaps, evaluates eligibility,
and categorizes opportunities into Paid Internships, Research Fellowships, and Unpaid/Undisclosed.
"""

import logging
import re
from typing import Any, Dict, List, Tuple
from src.config import CANDIDATE_PROFILE, EXPANDED_SKILL_LEXICON

logger = logging.getLogger("InternshipJARVIS.Matcher")

# Specific regex patterns for candidate skills to prevent substring false positives
SKILL_PATTERNS = {
    "python": re.compile(r"\bpython\b", re.IGNORECASE),
    "c": re.compile(
        r"(?<![&A-Za-z0-9])\bc\b(?![+#A-Za-z0-9])(?=.*?(?:programming|developer|embedded|software|systems|code|compiler|linux|c\+\+|algorithms))"
        r"|\b(?:c\s*\/\s*c\+\+|c\s*,\s*c\+\+|c\s+or\s+c\+\+|programming\s+in\s+c|c\s+language|ansi\s+c)\b",
        re.IGNORECASE,
    ),
    "sql": re.compile(r"\bsql\b", re.IGNORECASE),
    "html": re.compile(r"\bhtml5?\b", re.IGNORECASE),
    "css": re.compile(r"\bcss3?\b", re.IGNORECASE),
    "javascript": re.compile(r"\b(?:javascript|js)\b", re.IGNORECASE),
    "git": re.compile(r"\b(?:git|github|gitlab)\b", re.IGNORECASE),
}

# Compiled regex for missing skill lexicon detection
EXPANDED_PATTERNS = {
    skill: re.compile(rf"\b{re.escape(skill)}\b", re.IGNORECASE)
    for skill in EXPANDED_SKILL_LEXICON
}


class InternshipMatcher:
    """Evaluates and scores internship postings against the candidate's profile."""

    def __init__(self, profile: Dict[str, Any] = CANDIDATE_PROFILE):
        self.profile = profile

    def evaluate_opportunity(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Assess a single job posting, calculating score, rationale, missing skills, and eligibility."""
        title = job.get("title", "")
        company = job.get("company", "")
        desc = job.get("description", "")
        terms = job.get("terms", "")
        degrees = job.get("degrees", "")
        full_text = f"{title} {desc} {terms} {degrees}".lower()

        # 1. Identify Candidate Skills present
        matched_skills: List[str] = []
        for skill_name, pattern in SKILL_PATTERNS.items():
            if pattern.search(full_text):
                matched_skills.append(skill_name.capitalize())

        # 2. Identify Missing / Desired in-demand skills mentioned in posting
        candidate_skills = {s.lower() for s in self.profile.get("skills", [])}
        missing_skills: List[str] = []
        for skill_name, pattern in EXPANDED_PATTERNS.items():
            if skill_name.lower() not in candidate_skills and pattern.search(full_text):
                # Format special acronyms properly
                formatted = {
                    "aws": "AWS", "gcp": "GCP", "ci/cd": "CI/CD", "nlp": "NLP",
                    "rest api": "REST API", "sql": "SQL", "api": "API",
                }.get(skill_name.lower(), skill_name.title())
                missing_skills.append(formatted)
        # Limit missing skills to top 4 to keep report clean
        missing_skills = missing_skills[:4]

        # 3. Assess Interest & Domain Alignment
        matched_interests: List[str] = []
        interest_keywords = {
            "Software Development": ["software", "developer", "swe", "backend", "frontend", "full stack", "web", "systems"],
            "AI / Machine Learning": ["ai", "machine learning", "ml", "deep learning", "nlp", "computer vision", "llm"],
            "Data Science": ["data science", "data analyst", "analytics", "data engineer"],
            "Technology Research": ["research", "fellowship", "lab", "scientist", "open source", "gsoc"],
        }
        for domain, keywords in interest_keywords.items():
            if any(re.search(rf"\b{re.escape(k)}\b", full_text) for k in keywords):
                matched_interests.append(domain)

        # 4. Check Eligibility & Student Level
        eligibility_notes: List[str] = []
        is_early_friendly = False

        # Positive signals
        early_signals = ["freshman", "sophomore", "undergraduate", "bachelor", "student", "intern", "2027", "2028"]
        if any(sig in full_text for sig in early_signals):
            is_early_friendly = True

        # Graduation year check
        if "2025" in full_text and not ("2027" in full_text or "2028" in full_text):
            eligibility_notes.append("Targeting graduating class of 2025/2026. Verify pre-final eligibility.")
        elif any(y in full_text for y in ["2027", "2028"]):
            eligibility_notes.append("Explicitly open to 2027/2028 batch (Ideal for 3rd semester).")
        else:
            eligibility_notes.append("Open to undergraduate Computer Science students.")

        # Degree check
        if "phd only" in full_text or "master's required" in full_text:
            eligibility_notes.append("Postgraduate degree preferred; check undergrad eligibility.")

        # 5. Compute Match Score (0 - 100)
        score = 0

        # A. Skills matching (Max 40 points)
        skill_count = len(matched_skills)
        if skill_count >= 3:
            score += 40
        elif skill_count == 2:
            score += 30
        elif skill_count == 1:
            score += 20
        else:
            # If standard software engineering role with Python / JS implied
            if "software" in full_text or "developer" in full_text or "python" in full_text:
                score += 15

        # B. Interest alignment (Max 25 points)
        if matched_interests:
            score += min(25, len(matched_interests) * 12)

        # C. Role level & early student friendliness (Max 25 points)
        title_lower = title.lower()
        if "intern" in title_lower or "trainee" in title_lower or "fellow" in title_lower:
            score += 20
        if is_early_friendly:
            score += 5

        # D. Degree / Field relevance (Max 10 points)
        if any(k in full_text for k in ["computer science", "b.tech", "engineering", "bachelor", "cse"]):
            score += 10

        # E. Exclusion / Penalty deductions
        for exc in self.profile.get("exclusion_keywords", []):
            if exc in title_lower:
                score -= 40
            elif exc in full_text:
                score -= 15

        # Clamp score between 0 and 100
        final_score = max(0, min(100, score))

        # 6. Generate Human-Readable Explanation
        reasons: List[str] = []
        if matched_skills:
            reasons.append(f"Matches your core skills: {', '.join(matched_skills)}")
        if matched_interests:
            reasons.append(f"Aligns with your interest in {', '.join(matched_interests)}")
        if is_early_friendly:
            reasons.append("Suitable for early undergrads (1st/2nd year / 3rd semester)")

        if not reasons:
            explanation = "Relevant technology opportunity matching general CSE undergraduate profile."
        else:
            explanation = "; ".join(reasons) + "."

        result = dict(job)
        result["match_score"] = final_score
        result["matched_skills"] = matched_skills
        result["missing_skills"] = missing_skills
        result["matched_interests"] = matched_interests
        result["eligibility_notes"] = " ".join(eligibility_notes)
        result["match_explanation"] = explanation

        return result

    def match_and_categorize(
        self,
        jobs: List[Dict[str, Any]],
        min_score: int = 40,
        max_per_section: int = 10,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Filter, score, and group opportunities into three distinct categories:
        1. Paid Tech Internships
        2. Research & Open Source Fellowships
        3. Other Matching / Unpaid / Undisclosed
        """
        paid_internships: List[Dict[str, Any]] = []
        research_opportunities: List[Dict[str, Any]] = []
        other_opportunities: List[Dict[str, Any]] = []

        seen_links = set()

        for raw_job in jobs:
            url = raw_job.get("url", "")
            if not url or url in seen_links:
                continue
            seen_links.add(url)

            evaluated = self.evaluate_opportunity(raw_job)
            if evaluated["match_score"] < min_score:
                continue

            # Categorize
            if evaluated.get("is_research"):
                research_opportunities.append(evaluated)
            elif evaluated.get("is_paid") is True:
                paid_internships.append(evaluated)
            else:
                other_opportunities.append(evaluated)

        # Sort each section descending by match score
        paid_internships.sort(key=lambda x: x["match_score"], reverse=True)
        research_opportunities.sort(key=lambda x: x["match_score"], reverse=True)
        other_opportunities.sort(key=lambda x: x["match_score"], reverse=True)

        return {
            "paid_internships": paid_internships[:max_per_section],
            "research_opportunities": research_opportunities[:max_per_section],
            "other_opportunities": other_opportunities[:max_per_section],
        }
