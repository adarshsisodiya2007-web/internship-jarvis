"""Main orchestrator for Internship JARVIS.

Workflow:
1. Initialize configuration and logging.
2. Load historical seen job IDs (duplicate prevention).
3. Fetch candidate opportunities across free legitimate sources.
4. Filter out duplicates, expired, and suspicious listings.
5. Match against candidate profile, evaluate eligibility, calculate match scores.
6. Categorize into Paid Internships, Research/Fellowships, and Undisclosed.
7. Dispatch daily digest report via EmailSender (HTML + plain text fallback).
8. Persist newly processed jobs to cache.
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set

from src.config import (
    CANDIDATE_PROFILE,
    DRY_RUN,
    LATEST_MATCHES_FILE,
    MAX_RESULTS_PER_SECTION,
    MIN_MATCH_SCORE,
    SEEN_JOBS_FILE,
)
from src.email_sender import EmailSender
from src.fetcher import InternshipFetcher
from src.matcher import InternshipMatcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("InternshipJARVIS")


def load_seen_jobs(cache_path: Path) -> Set[str]:
    """Load previously seen job IDs to prevent duplicate alerts."""
    if not cache_path.exists():
        return set()
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return set(data)
            elif isinstance(data, dict):
                return set(data.keys())
    except Exception as e:
        logger.warning("Could not read seen jobs file (%s): %s. Starting fresh.", cache_path, e)
    return set()


def save_seen_jobs(cache_path: Path, seen_ids: Set[str]) -> None:
    """Save seen job IDs to disk."""
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        # Keep recent 2000 entries to prevent infinite growth
        trimmed = list(seen_ids)[-2000:]
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(trimmed, f, indent=2)
        logger.info("Updated seen jobs cache (%d entries saved)", len(trimmed))
    except Exception as e:
        logger.error("Failed to save seen jobs cache: %s", e)


def run_pipeline(
    dry_run: bool = DRY_RUN,
    ignore_cache: bool = False,
    min_score: int = MIN_MATCH_SCORE,
    max_per_section: int = MAX_RESULTS_PER_SECTION,
) -> bool:
    """Execute the complete find-filter-match-send pipeline."""
    logger.info("=" * 60)
    logger.info("Starting Internship JARVIS Daily Run")
    logger.info(
        "Candidate: %s | %s | Sem %d",
        CANDIDATE_PROFILE["education"],
        CANDIDATE_PROFILE["college"],
        CANDIDATE_PROFILE["current_semester"],
    )
    logger.info("Skills: %s", ", ".join(CANDIDATE_PROFILE["skills"]))
    logger.info("Min Score Threshold: %d%%", min_score)
    logger.info("=" * 60)

    # 1. Load seen jobs
    seen_ids = load_seen_jobs(SEEN_JOBS_FILE) if not ignore_cache else set()
    logger.info("Loaded %d previously alerted job IDs", len(seen_ids))

    # 2. Fetch fresh postings from public APIs and verified career portals
    fetcher = InternshipFetcher()
    raw_jobs = fetcher.fetch_all()
    if not raw_jobs:
        logger.warning("No jobs retrieved from any source. Check internet connectivity.")
        return False

    # 3. Deduplicate against seen jobs
    unseen_jobs = [job for job in raw_jobs if job.get("id") not in seen_ids]
    logger.info("Fresh unseen postings to evaluate: %d", len(unseen_jobs))

    # 4. Score, evaluate eligibility, and categorize
    matcher = InternshipMatcher(profile=CANDIDATE_PROFILE)
    categorized = matcher.match_and_categorize(
        unseen_jobs if unseen_jobs else [],
        min_score=min_score,
        max_per_section=max_per_section,
    ) if unseen_jobs else {"paid_internships": [], "research_opportunities": [], "other_opportunities": []}

    paid_count = len(categorized["paid_internships"])
    research_count = len(categorized["research_opportunities"])
    other_count = len(categorized["other_opportunities"])
    total_selected = paid_count + research_count + other_count

    logger.info(
        "Matching results: Paid: %d | Research: %d | Other: %d | Total: %d",
        paid_count,
        research_count,
        other_count,
        total_selected,
    )

    if total_selected == 0:
        logger.info("No new unreviewed postings matched criteria above %d%% score. Sending 'All Caught Up' report.", min_score)

    # 5. Save latest matches snapshot for the Web Dashboard
    try:
        now_utc = datetime.now(timezone.utc)
        # If today's run found new items, write them out. If 0 new items were found, preserve existing cached jobs if available
        if total_selected > 0 or not LATEST_MATCHES_FILE.exists():
            dashboard_data = {
                "updated_at": now_utc.isoformat(),
                "updated_at_readable": now_utc.strftime("%d %b %Y, %I:%M %p UTC"),
                "total_found": len(raw_jobs),
                "total_matching": total_selected,
                "stats": {
                    "paid": paid_count,
                    "research": research_count,
                    "other": other_count,
                },
                "candidate": {
                    "education": CANDIDATE_PROFILE["education"],
                    "college": CANDIDATE_PROFILE["college"],
                    "semester": CANDIDATE_PROFILE["current_semester"],
                    "graduation_year": CANDIDATE_PROFILE.get("graduation_year", 2029),
                    "skills": CANDIDATE_PROFILE["skills"],
                },
                "categorized_jobs": categorized,
            }
            with open(LATEST_MATCHES_FILE, "w", encoding="utf-8") as f:
                json.dump(dashboard_data, f, indent=2)
            logger.info("Saved latest matches snapshot to %s", LATEST_MATCHES_FILE)
        else:
            # Preserve existing job data, just update scan timestamp
            try:
                with open(LATEST_MATCHES_FILE, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
                existing_data["updated_at"] = now_utc.isoformat()
                existing_data["updated_at_readable"] = now_utc.strftime("%d %b %Y, %I:%M %p UTC")
                existing_data["total_found"] = len(raw_jobs)
                with open(LATEST_MATCHES_FILE, "w", encoding="utf-8") as f:
                    json.dump(existing_data, f, indent=2)
                logger.info("Updated scan timestamp in %s", LATEST_MATCHES_FILE)
            except Exception as e_inner:
                logger.warning("Could not update existing snapshot timestamp: %s", e_inner)
    except Exception as e:
        logger.warning("Could not save latest matches file: %s", e)

    # 6. Dispatch email or write local HTML report
    sender = EmailSender()
    sender.dry_run = dry_run
    send_success = sender.send_report(categorized)

    # 7. Update seen jobs cache if send or dry-run was successful
    if send_success and not ignore_cache:
        for cat in categorized.values():
            for item in cat:
                if item.get("id"):
                    seen_ids.add(item["id"])
        save_seen_jobs(SEEN_JOBS_FILE, seen_ids)

    logger.info("=" * 60)
    logger.info("Internship JARVIS run completed successfully!")
    logger.info("=" * 60)
    return send_success


def main():
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description="Internship JARVIS - Automated Internship Matcher")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=DRY_RUN,
        help="Generate local HTML report without sending live email",
    )
    parser.add_argument(
        "--ignore-cache",
        action="store_true",
        help="Ignore previously seen jobs and evaluate all fetched postings",
    )
    parser.add_argument(
        "--min-score",
        type=int,
        default=MIN_MATCH_SCORE,
        help=f"Minimum match score (default: {MIN_MATCH_SCORE})",
    )
    parser.add_argument(
        "--max-per-section",
        type=int,
        default=MAX_RESULTS_PER_SECTION,
        help=f"Maximum opportunities per category (default: {MAX_RESULTS_PER_SECTION})",
    )

    args = parser.parse_args()
    success = run_pipeline(
        dry_run=args.dry_run,
        ignore_cache=args.ignore_cache,
        min_score=args.min_score,
        max_per_section=args.max_per_section,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
