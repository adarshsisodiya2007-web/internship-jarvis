"""Web Dashboard application for Internship JARVIS.

Provides a clean, responsive web interface displaying verified matches, KPI stats,
and opportunity details without exposing sensitive credentials or logs.
Includes /health check endpoint for Render and debounced on-demand refresh.
"""

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import requests
from flask import Flask, jsonify, render_template, request

from src.config import (
    BASE_DIR,
    CANDIDATE_PROFILE,
    LATEST_MATCHES_FILE,
    MAX_RESULTS_PER_SECTION,
    MIN_MATCH_SCORE,
)
from src.fetcher import InternshipFetcher
from src.matcher import InternshipMatcher

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("InternshipJARVIS.Web")

# Initialize Flask
template_dir = BASE_DIR / "src" / "templates"
app = Flask(__name__, template_folder=str(template_dir))

# State & Cooldown management for safe refresh
REFRESH_COOLDOWN_SECONDS = 60
_last_refresh_timestamp = 0
_in_memory_data: Dict[str, Any] = {}

# Raw GitHub URL for remote state synchronization across ephemeral Render deploys
GITHUB_RAW_DATA_URL = (
    "https://raw.githubusercontent.com/adarshsisodiya2007-web/internship-jarvis/main/data/latest_matches.json"
)


def load_dashboard_data() -> Dict[str, Any]:
    """Load latest match snapshot from local disk, GitHub raw sync, or in-memory fallback."""
    global _in_memory_data

    # 1. Check local file on disk
    if LATEST_MATCHES_FILE.exists():
        try:
            with open(LATEST_MATCHES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data and "categorized_jobs" in data:
                    _in_memory_data = data
                    return data
        except Exception as e:
            logger.warning("Could not read local matches file: %s", e)

    # 2. Check in-memory cached copy
    if _in_memory_data and "categorized_jobs" in _in_memory_data:
        return _in_memory_data

    # 3. Fetch latest data from GitHub repository raw content (Render ephemeral disk support)
    try:
        resp = requests.get(GITHUB_RAW_DATA_URL, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            if data and "categorized_jobs" in data:
                _in_memory_data = data
                # Cache locally if possible
                try:
                    with open(LATEST_MATCHES_FILE, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
                except Exception:
                    pass
                return data
    except Exception as e:
        logger.info("Could not fetch remote GitHub snapshot: %s", e)

    # 4. Fallback: Generate empty initial template structure
    now_utc = datetime.now(timezone.utc)
    return {
        "updated_at": now_utc.isoformat(),
        "updated_at_readable": now_utc.strftime("%d %b %Y, %I:%M %p UTC"),
        "total_found": 0,
        "total_matching": 0,
        "min_score": MIN_MATCH_SCORE,
        "stats": {"paid": 0, "research": 0, "other": 0},
        "candidate": {
            "education": CANDIDATE_PROFILE["education"],
            "college": CANDIDATE_PROFILE["college"],
            "semester": CANDIDATE_PROFILE["current_semester"],
            "graduation_year": CANDIDATE_PROFILE.get("graduation_year", 2029),
            "skills": CANDIDATE_PROFILE["skills"],
        },
        "categorized_jobs": {
            "paid_internships": [],
            "research_opportunities": [],
            "other_opportunities": [],
        },
    }


def perform_live_refresh() -> Dict[str, Any]:
    """Execute in-memory search and match without sending any email."""
    global _in_memory_data, _last_refresh_timestamp

    logger.info("Performing on-demand live scan from dashboard...")
    fetcher = InternshipFetcher()
    raw_jobs = fetcher.fetch_all()

    matcher = InternshipMatcher(profile=CANDIDATE_PROFILE)
    categorized = matcher.match_and_categorize(
        raw_jobs,
        min_score=MIN_MATCH_SCORE,
        max_per_section=MAX_RESULTS_PER_SECTION,
    )

    paid_count = len(categorized["paid_internships"])
    research_count = len(categorized["research_opportunities"])
    other_count = len(categorized["other_opportunities"])
    total_matching = paid_count + research_count + other_count

    now_utc = datetime.now(timezone.utc)
    snapshot = {
        "updated_at": now_utc.isoformat(),
        "updated_at_readable": now_utc.strftime("%d %b %Y, %I:%M %p UTC"),
        "total_found": len(raw_jobs),
        "total_matching": total_matching,
        "min_score": MIN_MATCH_SCORE,
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

    _in_memory_data = snapshot
    _last_refresh_timestamp = time.time()

    # Save to disk as well
    try:
        with open(LATEST_MATCHES_FILE, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, indent=2)
    except Exception as e:
        logger.warning("Could not persist refreshed data: %s", e)

    return snapshot


@app.route("/")
def index():
    """Render the main responsive dashboard."""
    data = load_dashboard_data()
    return render_template("index.html", data=data)


@app.route("/api/refresh", methods=["POST", "GET"])
def refresh():
    """Manual refresh endpoint with safe cooldown debouncing."""
    global _last_refresh_timestamp

    # Check cooldown from both in-memory timestamp and file mtime
    file_elapsed = 999.0
    if LATEST_MATCHES_FILE.exists():
        try:
            file_elapsed = time.time() - LATEST_MATCHES_FILE.stat().st_mtime
        except Exception:
            pass

    mem_elapsed = (time.time() - _last_refresh_timestamp) if _last_refresh_timestamp > 0 else 999.0
    elapsed = min(file_elapsed, mem_elapsed)

    if elapsed < REFRESH_COOLDOWN_SECONDS:
        remaining = max(1, int(REFRESH_COOLDOWN_SECONDS - elapsed))
        return jsonify({
            "success": True,
            "cooldown": True,
            "message": f"Scan was recently performed. Please wait {remaining}s before rescanning.",
            "remaining_seconds": remaining,
        })

    try:
        snapshot = perform_live_refresh()
        return jsonify({
            "success": True,
            "cooldown": False,
            "message": f"Scan complete! Found {snapshot['total_matching']} verified opportunities.",
            "total_matching": snapshot["total_matching"],
        })
    except Exception as e:
        logger.error("Refresh failed: %s", e)
        return jsonify({
            "success": False,
            "message": f"Scan encountered an error: {str(e)}",
        }), 500


@app.route("/health")
def health():
    """Health check endpoint for Render and uptime monitors."""
    data = load_dashboard_data()
    return jsonify({
        "status": "ok",
        "service": "Internship JARVIS",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cached_opportunities": data.get("total_matching", 0),
        "total_found": data.get("total_found", 0),
    }), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
