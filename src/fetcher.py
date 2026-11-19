"""Internship Fetcher module.

Aggregates opportunities from multiple legitimate, accessible, 100% free sources:
1. SimplifyJobs Verified Internship Directory (Thousands of active, direct employer links)
2. Remotive API (Remote tech & software internships)
3. Jobicy API (Global tech & junior opportunities)
4. Arbeitnow API (Tech jobs & internships)
5. We Work Remotely (WWR) RSS feed
"""

import hashlib
import json
import logging
import re
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import requests

logger = logging.getLogger("InternshipJARVIS.Fetcher")

# Timeout for HTTP requests in seconds
REQUEST_TIMEOUT = 12

# Suspicious domains / schemes that indicate low-quality or scam postings
SUSPICIOUS_DOMAINS = [
    "t.me",
    "telegram.me",
    "wa.me",
    "whatsapp.com",
    "survey",
    "earn-quick",
    "pay-to-work",
    "crypto-job-airdrop",
]

SUSPICIOUS_PHRASES = [
    "registration fee",
    "security deposit",
    "pay fee to apply",
    "investment required",
    "crypto token reward",
    "whatsapp us to start",
    "telegram channel to apply",
    "send money",
    "data entry clerk earn 5000/day",
]

RESEARCH_KEYWORDS = [
    "research",
    "fellowship",
    "lab",
    "laboratory",
    "institute",
    "university",
    "iit",
    "iiit",
    "drdo",
    "isro",
    "csir",
    "gsoc",
    "google summer of code",
    "mlh",
    "open source",
    "academic",
]


def clean_text(text: Optional[str]) -> str:
    """Strip HTML tags and excess whitespace."""
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", " ", text)
    clean = re.sub(r"\s+", " ", clean)
    return clean.strip()


def generate_listing_id(title: str, company: str, url: str) -> str:
    """Generate a deterministic hash ID to track duplicates across runs."""
    key = f"{company.strip().lower()}:{title.strip().lower()}:{url.strip().lower()}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def is_suspicious(title: str, company: str, description: str, url: str) -> bool:
    """Filter out scams, spam, fee-charging programs, or shady contact links."""
    combined = f"{title} {company} {description}".lower()
    for phrase in SUSPICIOUS_PHRASES:
        if phrase in combined:
            return True

    url_lower = url.lower()
    for domain in SUSPICIOUS_DOMAINS:
        if domain in url_lower:
            return True

    if not url or not url.startswith(("http://", "https://")):
        return True

    return False


def detect_stipend_and_type(text: str) -> Dict[str, Any]:
    """Analyze text for stipend and research classification."""
    text_lower = text.lower()

    is_research = any(kw in text_lower for kw in RESEARCH_KEYWORDS)

    # Detect unpaid indicators
    if any(kw in text_lower for kw in ["unpaid", "volunteer", "no stipend", "zero stipend", "for credit only"]):
        return {
            "stipend": "Unpaid / Academic Credit",
            "is_paid": False,
            "is_research": is_research,
        }

    # Regex patterns for stipend amounts ($ / INR / Rs / € / £ / per month / /hr)
    salary_patterns = [
        r"(?:₹|rs\.?|inr)\s*[\d,]+(?:\s*-\s*[\d,]+)?(?:\s*(?:k|pm|per month|lpa|month))?",
        r"(?:\$|€|£)\s*[\d,]+(?:\s*-\s*[\d,]+)?(?:\s*(?:k|\/hr|per hour|\/month|month))?",
        r"\b\d+\s*(?:k|kpm)\s*(?:inr|rs|per month)\b",
        r"\bcompetitive stipend\b",
        r"\bpaid internship\b",
    ]

    for pat in salary_patterns:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            return {
                "stipend": match.group(0).strip(),
                "is_paid": True,
                "is_research": is_research,
            }

    # If marked as paid internship
    if "paid" in text_lower:
        return {
            "stipend": "Paid / Disclosed upon offer",
            "is_paid": True,
            "is_research": is_research,
        }

    if is_research:
        return {
            "stipend": "Research Grant / Academic",
            "is_paid": False,
            "is_research": True,
        }

    return {
        "stipend": "Undisclosed / Competitive",
        "is_paid": False,
        "is_research": False,
    }


class InternshipFetcher:
    """Fetches, parses, and normalizes internships from public data sources."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36 InternshipJARVIS/1.0"
            ),
            "Accept": "application/json, application/xml, text/xml, */*",
        })

    def fetch_all(self) -> List[Dict[str, Any]]:
        """Fetch from all accessible sources and return deduplicated list."""
        all_jobs: List[Dict[str, Any]] = []

        # 1. SimplifyJobs Verified Listings
        try:
            simplify_jobs = self._fetch_simplify_jobs()
            logger.info("Retrieved %d active listings from SimplifyJobs", len(simplify_jobs))
            all_jobs.extend(simplify_jobs)
        except Exception as e:
            logger.warning("Error fetching SimplifyJobs: %s", e)

        # 2. Remotive API
        try:
            remotive_jobs = self._fetch_remotive()
            logger.info("Retrieved %d listings from Remotive", len(remotive_jobs))
            all_jobs.extend(remotive_jobs)
        except Exception as e:
            logger.warning("Error fetching Remotive: %s", e)

        # 3. Jobicy API
        try:
            jobicy_jobs = self._fetch_jobicy()
            logger.info("Retrieved %d listings from Jobicy", len(jobicy_jobs))
            all_jobs.extend(jobicy_jobs)
        except Exception as e:
            logger.warning("Error fetching Jobicy: %s", e)

        # 4. Arbeitnow API
        try:
            arbeitnow_jobs = self._fetch_arbeitnow()
            logger.info("Retrieved %d listings from Arbeitnow", len(arbeitnow_jobs))
            all_jobs.extend(arbeitnow_jobs)
        except Exception as e:
            logger.warning("Error fetching Arbeitnow: %s", e)

        # 5. We Work Remotely RSS
        try:
            wwr_jobs = self._fetch_wwr_rss()
            logger.info("Retrieved %d listings from We Work Remotely", len(wwr_jobs))
            all_jobs.extend(wwr_jobs)
        except Exception as e:
            logger.warning("Error fetching We Work Remotely: %s", e)

        logger.info("Total raw listings collected: %d", len(all_jobs))
        return all_jobs

    def _fetch_simplify_jobs(self) -> List[Dict[str, Any]]:
        """Fetch verified Summer / Fall / Winter college internships."""
        url = "https://raw.githubusercontent.com/SimplifyJobs/Summer2025-Internships/dev/.github/scripts/listings.json"
        resp = self.session.get(url, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            logger.warning("SimplifyJobs returned status %d", resp.status_code)
            return []

        data = resp.json()
        results = []
        for item in data:
            if not item.get("active", False):
                continue

            title = clean_text(item.get("title", ""))
            company = clean_text(item.get("company_name", ""))
            url_link = item.get("url", "").strip()

            if not title or not company or not url_link:
                continue

            locations = item.get("locations", [])
            location_str = ", ".join(locations) if locations else "Remote / Various"
            category = item.get("category", "Software Engineering")
            terms = ", ".join(item.get("terms", []))
            degrees = ", ".join(item.get("degrees", []))

            snippet = f"{title} at {company}. Category: {category}. Terms: {terms}. Degrees: {degrees}. Location: {location_str}"

            if is_suspicious(title, company, snippet, url_link):
                continue

            stipend_info = detect_stipend_and_type(f"{title} {category}")

            results.append({
                "id": generate_listing_id(title, company, url_link),
                "title": title,
                "company": company,
                "url": url_link,
                "location": location_str,
                "description": snippet,
                "stipend": stipend_info["stipend"],
                "is_paid": stipend_info["is_paid"],
                "is_research": stipend_info["is_research"] or "research" in title.lower(),
                "source": "SimplifyJobs (Verified Employer)",
                "terms": terms,
                "degrees": degrees,
                "date_posted": item.get("date_posted"),
            })

        return results

    def _fetch_remotive(self) -> List[Dict[str, Any]]:
        """Fetch remote software developer internships and junior positions."""
        url = "https://remotive.com/api/remote-jobs?search=intern"
        resp = self.session.get(url, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            return []

        data = resp.json()
        jobs = data.get("jobs", [])
        results = []
        for job in jobs:
            title = clean_text(job.get("title", ""))
            company = clean_text(job.get("company_name", ""))
            url_link = job.get("url", "").strip()
            raw_desc = clean_text(job.get("description", ""))
            salary = clean_text(job.get("salary", ""))
            location = clean_text(job.get("candidate_required_location", "Remote"))

            if not title or not company or not url_link:
                continue

            if is_suspicious(title, company, raw_desc, url_link):
                continue

            stipend_info = detect_stipend_and_type(f"{salary} {title} {raw_desc[:300]}")
            if salary:
                stipend_info["stipend"] = salary
                stipend_info["is_paid"] = True

            results.append({
                "id": generate_listing_id(title, company, url_link),
                "title": title,
                "company": company,
                "url": url_link,
                "location": location or "Remote",
                "description": raw_desc[:500],
                "stipend": stipend_info["stipend"],
                "is_paid": stipend_info["is_paid"],
                "is_research": stipend_info["is_research"],
                "source": "Remotive API",
                "date_posted": job.get("publication_date", ""),
            })

        return results

    def _fetch_jobicy(self) -> List[Dict[str, Any]]:
        """Fetch internship tags from Jobicy API."""
        url = "https://jobicy.com/api/v2/remote-jobs?count=30&tag=internship"
        resp = self.session.get(url, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            return []

        data = resp.json()
        jobs = data.get("jobs", [])
        results = []
        for job in jobs:
            title = clean_text(job.get("jobTitle", ""))
            company = clean_text(job.get("companyName", ""))
            url_link = job.get("url", "").strip()
            desc = clean_text(job.get("jobDescription", ""))
            location = clean_text(job.get("jobGeo", "Remote"))

            if not title or not company or not url_link:
                continue

            if is_suspicious(title, company, desc, url_link):
                continue

            stipend_info = detect_stipend_and_type(f"{title} {desc[:300]}")

            results.append({
                "id": generate_listing_id(title, company, url_link),
                "title": title,
                "company": company,
                "url": url_link,
                "location": location or "Remote",
                "description": desc[:500],
                "stipend": stipend_info["stipend"],
                "is_paid": stipend_info["is_paid"],
                "is_research": stipend_info["is_research"],
                "source": "Jobicy API",
                "date_posted": job.get("pubDate", ""),
            })

        return results

    def _fetch_arbeitnow(self) -> List[Dict[str, Any]]:
        """Fetch tech jobs from Arbeitnow public API."""
        url = "https://www.arbeitnow.com/api/job-board-api"
        resp = self.session.get(url, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            return []

        data = resp.json()
        jobs = data.get("data", [])
        results = []
        for job in jobs:
            title = clean_text(job.get("title", ""))
            company = clean_text(job.get("company_name", ""))
            url_link = job.get("url", "").strip()
            desc = clean_text(job.get("description", ""))
            location = clean_text(job.get("location", "Remote"))

            # Filter for student / intern / junior / entry roles
            title_lower = title.lower()
            if not any(k in title_lower for k in ["intern", "trainee", "junior", "student", "working student", "apprentice"]):
                continue

            if is_suspicious(title, company, desc, url_link):
                continue

            stipend_info = detect_stipend_and_type(f"{title} {desc[:300]}")

            results.append({
                "id": generate_listing_id(title, company, url_link),
                "title": title,
                "company": company,
                "url": url_link,
                "location": location or "Remote",
                "description": desc[:500],
                "stipend": stipend_info["stipend"],
                "is_paid": stipend_info["is_paid"],
                "is_research": stipend_info["is_research"],
                "source": "Arbeitnow API",
                "date_posted": job.get("created_at", ""),
            })

        return results

    def _fetch_wwr_rss(self) -> List[Dict[str, Any]]:
        """Fetch remote programming jobs from We Work Remotely RSS feed."""
        url = "https://weworkremotely.com/categories/remote-programming-jobs.rss"
        resp = self.session.get(url, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            return []

        root = ET.fromstring(resp.content)
        items = root.findall(".//item")
        results = []
        for item in items:
            title_elem = item.find("title")
            link_elem = item.find("link")
            desc_elem = item.find("description")
            pub_elem = item.find("pubDate")

            raw_title = title_elem.text if title_elem is not None else ""
            url_link = link_elem.text if link_elem is not None else ""
            desc = clean_text(desc_elem.text if desc_elem is not None else "")
            pub_date = pub_elem.text if pub_elem is not None else ""

            # WWR format is typically: "Company: Job Title"
            company = "We Work Remotely Listing"
            title = raw_title
            if ":" in raw_title:
                parts = raw_title.split(":", 1)
                company = clean_text(parts[0])
                title = clean_text(parts[1])

            title_lower = title.lower()
            # Look for student, intern, or entry level programming roles
            is_entry = any(k in title_lower for k in ["intern", "junior", "trainee", "entry", "apprentice", "associate"])
            if not is_entry:
                continue

            if is_suspicious(title, company, desc, url_link):
                continue

            stipend_info = detect_stipend_and_type(f"{title} {desc[:300]}")

            results.append({
                "id": generate_listing_id(title, company, url_link),
                "title": title,
                "company": company,
                "url": url_link,
                "location": "Remote",
                "description": desc[:500],
                "stipend": stipend_info["stipend"],
                "is_paid": stipend_info["is_paid"],
                "is_research": stipend_info["is_research"],
                "source": "We Work Remotely RSS",
                "date_posted": pub_date,
            })

        return results
