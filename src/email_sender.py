"""Email Sender module for Internship JARVIS.

Constructs responsive HTML and plain-text email digests, formats match scores,
skill badges, eligibility warnings, and application links, and delivers them via Gmail SMTP.
"""

import email.message
import html
import logging
import smtplib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from src.config import (
    CANDIDATE_PROFILE,
    DASHBOARD_URL,
    DRY_RUN,
    GMAIL_APP_PASSWORD,
    GMAIL_USER,
    RECIPIENT_EMAIL,
    REPORTS_DIR,
)

logger = logging.getLogger("InternshipJARVIS.EmailSender")


def get_score_color(score: int) -> str:
    """Return hex color matching score quality."""
    if score >= 80:
        return "#10B981"  # Emerald green
    if score >= 60:
        return "#3B82F6"  # Royal blue
    return "#F59E0B"  # Amber


def render_job_card_html(job: Dict[str, Any]) -> str:
    """Render a single job item into a clean HTML card."""
    title = html.escape(job.get("title", "Untitled Role"))
    company = html.escape(job.get("company", "Company"))
    url = job.get("url", "#")
    location = html.escape(job.get("location", "Remote / Various"))
    stipend = html.escape(job.get("stipend", "Undisclosed"))
    score = job.get("match_score", 0)
    score_color = get_score_color(score)
    source = html.escape(job.get("source", "Verified Source"))

    matched_skills = job.get("matched_skills", [])
    missing_skills = job.get("missing_skills", [])
    explanation = html.escape(job.get("match_explanation", ""))
    eligibility = html.escape(job.get("eligibility_notes", ""))

    matched_chips = "".join(
        f'<span style="display:inline-block; background-color:#E0F2FE; color:#0369A1; font-size:11px; font-weight:600; padding:2px 8px; border-radius:12px; margin-right:4px; margin-bottom:4px;">✓ {html.escape(s)}</span>'
        for s in matched_skills
    ) or '<span style="font-size:11px; color:#6B7280;">General CS Foundation</span>'

    missing_chips = "".join(
        f'<span style="display:inline-block; background-color:#FEF3C7; color:#B45309; font-size:11px; font-weight:600; padding:2px 8px; border-radius:12px; margin-right:4px; margin-bottom:4px;">+ {html.escape(s)}</span>'
        for s in missing_skills
    ) if missing_skills else '<span style="font-size:11px; color:#10B981;">No major skill gaps identified</span>'

    return f"""
    <div style="background-color:#ffffff; border:1px solid #E5E7EB; border-radius:10px; padding:18px; margin-bottom:16px; box-shadow:0 1px 3px rgba(0,0,0,0.05);">
        <table style="width:100%; border-collapse:collapse;">
            <tr>
                <td style="vertical-align:top;">
                    <div style="font-size:18px; font-weight:700; color:#111827; line-height:1.3;">{title}</div>
                    <div style="font-size:14px; font-weight:600; color:#4B5563; margin-top:4px;">{company} &bull; <span style="font-weight:400; color:#6B7280;">{location}</span></div>
                </td>
                <td style="text-align:right; vertical-align:top; white-space:nowrap; padding-left:10px;">
                    <span style="display:inline-block; background-color:{score_color}; color:#ffffff; font-size:12px; font-weight:700; padding:4px 10px; border-radius:20px;">
                        {score}% Match
                    </span>
                    <div style="font-size:11px; color:#9CA3AF; margin-top:4px;">{source}</div>
                </td>
            </tr>
        </table>

        <!-- Metadata row -->
        <div style="margin-top:12px; padding:8px 12px; background-color:#F9FAFB; border-radius:6px; font-size:12px; color:#374151;">
            <strong>Stipend / Comp:</strong> <span style="color:#059669; font-weight:600;">{stipend}</span>
            &nbsp;|&nbsp;
            <strong>Eligibility Note:</strong> {eligibility}
        </div>

        <!-- Rationale -->
        <div style="margin-top:10px; font-size:13px; color:#4B5563; line-height:1.4;">
            <strong>Why it matches:</strong> {explanation}
        </div>

        <!-- Skills breakdown -->
        <div style="margin-top:10px;">
            <div style="font-size:11px; font-weight:600; color:#374151; margin-bottom:4px;">Your Matching Skills:</div>
            <div>{matched_chips}</div>
        </div>
        <div style="margin-top:8px;">
            <div style="font-size:11px; font-weight:600; color:#374151; margin-bottom:4px;">Recommended Skills to Highlight / Learn:</div>
            <div>{missing_chips}</div>
        </div>

        <!-- Apply CTA -->
        <div style="margin-top:14px; text-align:right;">
            <a href="{url}" target="_blank" style="display:inline-block; background-color:#1E3A8A; color:#ffffff; font-size:13px; font-weight:600; padding:8px 16px; border-radius:6px; text-decoration:none;">
                Official Application Link &rarr;
            </a>
        </div>
    </div>
    """


def generate_email_html(categorized_jobs: Dict[str, List[Dict[str, Any]]]) -> str:
    """Generate complete responsive HTML email document."""
    paid = categorized_jobs.get("paid_internships", [])
    research = categorized_jobs.get("research_opportunities", [])
    other = categorized_jobs.get("other_opportunities", [])
    total_count = len(paid) + len(research) + len(other)

    now_ist = datetime.now(timezone.utc).strftime("%d %b %Y, %I:%M %p UTC")
    dash_url = DASHBOARD_URL or "https://internship-jarvis.onrender.com/"

    if total_count == 0:
        content_body = f"""
        <div style="text-align:center; padding:32px 16px;">
            <div style="font-size:48px; margin-bottom:12px;">✅</div>
            <h2 style="font-size:20px; font-weight:700; color:#0F172A; margin:0 0 8px 0;">All Caught Up for Today!</h2>
            <p style="font-size:14px; color:#64748B; line-height:1.5; max-width:480px; margin:0 auto 20px auto;">
                Internship JARVIS scanned all public sources today. There are currently no new unreviewed opportunities matching your profile criteria above the scoring threshold.
            </p>
            <div style="margin:24px 0;">
                <a href="{dash_url}" target="_blank" style="display:inline-block; background-color:#2563EB; color:#ffffff; font-size:14px; font-weight:600; padding:10px 22px; border-radius:8px; text-decoration:none; box-shadow:0 2px 4px rgba(37,99,235,0.3);">
                    View All Active Opportunities on Dashboard &rarr;
                </a>
            </div>
            <p style="font-size:12px; color:#94A3B8;">
                JARVIS will automatically run again tomorrow at 9:00 PM IST to capture new postings.
            </p>
        </div>
        """
    else:
        paid_cards = "".join(render_job_card_html(j) for j in paid) or "<p style='color:#6B7280; font-size:13px;'>No new paid internships above threshold today.</p>"
        research_cards = "".join(render_job_card_html(j) for j in research) or "<p style='color:#6B7280; font-size:13px;'>No new research or open-source fellowship postings today.</p>"
        other_cards = "".join(render_job_card_html(j) for j in other) or "<p style='color:#6B7280; font-size:13px;'>No other listings matching threshold today.</p>"

        content_body = f"""
            <!-- Dashboard Banner Button -->
            <div style="background-color:#EFF6FF; border:1px solid #BFDBFE; border-radius:8px; padding:12px 16px; margin-bottom:24px; text-align:center;">
                <span style="font-size:13px; color:#1E40AF; font-weight:600;">Want to filter or bookmark these roles interactively?</span>
                <div style="margin-top:6px;">
                    <a href="{dash_url}" target="_blank" style="display:inline-block; background-color:#2563EB; color:#ffffff; font-size:12px; font-weight:600; padding:6px 14px; border-radius:6px; text-decoration:none;">
                        Open Live Web Dashboard &rarr;
                    </a>
                </div>
            </div>

            <!-- Category 1: Paid Internships -->
            <div style="margin-bottom:28px;">
                <h2 style="font-size:18px; font-weight:700; color:#0F172A; border-bottom:2px solid #E2E8F0; padding-bottom:8px; margin-bottom:14px;">
                    💰 High-Match Paid Tech Internships ({len(paid)})
                </h2>
                {paid_cards}
            </div>

            <!-- Category 2: Research & Fellowships -->
            <div style="margin-bottom:28px;">
                <h2 style="font-size:18px; font-weight:700; color:#0F172A; border-bottom:2px solid #E2E8F0; padding-bottom:8px; margin-bottom:14px;">
                    🔬 Research & Open-Source Fellowships ({len(research)})
                </h2>
                {research_cards}
            </div>

            <!-- Category 3: Other / Undisclosed -->
            <div style="margin-bottom:24px;">
                <h2 style="font-size:18px; font-weight:700; color:#0F172A; border-bottom:2px solid #E2E8F0; padding-bottom:8px; margin-bottom:14px;">
                    📋 Other Relevant Opportunities ({len(other)})
                </h2>
                {other_cards}
            </div>
        """

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Internship JARVIS Daily Report</title>
</head>
<body style="margin:0; padding:0; background-color:#F3F4F6; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color:#1F2937;">
    <div style="max-width:680px; margin:24px auto; background-color:#FFFFFF; border-radius:12px; overflow:hidden; box-shadow:0 4px 6px -1px rgba(0,0,0,0.1);">
        
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 100%); color:#FFFFFF; padding:28px 24px; text-align:left;">
            <div style="font-size:12px; font-weight:700; letter-spacing:1px; text-transform:uppercase; color:#93C5FD;">AUTOMATED INTELLIGENCE DIGEST</div>
            <h1 style="margin:6px 0 0 0; font-size:24px; font-weight:800; color:#FFFFFF;">⚡ Internship JARVIS</h1>
            <p style="margin:6px 0 0 0; font-size:13px; color:#E2E8F0;">
                Curated for <strong>{CANDIDATE_PROFILE['education']}</strong> ({CANDIDATE_PROFILE['college']}) &bull; Sem {CANDIDATE_PROFILE['current_semester']} (Class of {CANDIDATE_PROFILE.get('graduation_year', 2029)})
            </p>
            <div style="margin-top:12px; font-size:12px; color:#93C5FD;">
                Dispatched: {now_ist} &bull; Curated Matches: <strong>{total_count}</strong>
            </div>
        </div>

        <div style="padding:24px;">
            {content_body}

            <!-- Profile Summary Box -->
            <div style="background-color:#F8FAFC; border:1px dashed #CBD5E1; border-radius:8px; padding:14px; font-size:12px; color:#64748B; margin-top:20px;">
                <strong>Active Profile Filter:</strong> Python, C, SQL, HTML, CSS, JavaScript, Git &bull; Target: 1st/2nd Year undergrad opportunities (Class of 2028/2029) &bull; Verified sources only.
            </div>
        </div>

        <!-- Footer -->
        <div style="background-color:#F8FAFC; border-top:1px solid #E2E8F0; padding:18px 24px; text-align:center; font-size:12px; color:#64748B;">
            <p style="margin:0 0 6px 0;">
                Internship JARVIS runs autonomously via GitHub Actions every evening at 9 PM IST.
            </p>
            <p style="margin:0 0 8px 0;">
                <a href="{dash_url}" target="_blank" style="color:#2563EB; text-decoration:none; font-weight:600;">
                    🌐 Open Live Web Dashboard ({dash_url})
                </a>
            </p>
            <p style="margin:0; font-size:11px; color:#94A3B8;">
                Legitimate career advisory notice: Never pay any application fee or share financial details with employers.
            </p>
        </div>

    </div>
</body>
</html>
"""


def generate_email_text(categorized_jobs: Dict[str, List[Dict[str, Any]]]) -> str:
    """Generate clean plain text fallback email."""
    dash_url = DASHBOARD_URL or "https://internship-jarvis.onrender.com/"
    paid = categorized_jobs.get("paid_internships", [])
    research = categorized_jobs.get("research_opportunities", [])
    other = categorized_jobs.get("other_opportunities", [])
    total_count = len(paid) + len(research) + len(other)

    lines = [
        "=" * 60,
        "INTERNSHIP JARVIS - DAILY REPORT",
        f"Candidate: {CANDIDATE_PROFILE['education']}, Sem {CANDIDATE_PROFILE['current_semester']} (Class of {CANDIDATE_PROFILE.get('graduation_year', 2029)})",
        f"Live Web Dashboard: {dash_url}",
        "=" * 60,
        "",
    ]

    if total_count == 0:
        lines.append("ALL CAUGHT UP FOR TODAY")
        lines.append("-" * 40)
        lines.append("Internship JARVIS scanned all verified public sources today.")
        lines.append("There are no new unreviewed opportunities matching your profile above the score threshold.")
        lines.append(f"Explore existing opportunities on your live dashboard: {dash_url}")
        lines.append("")
    else:
        for cat_name, key in [
            ("PAID TECH INTERNSHIPS", "paid_internships"),
            ("RESEARCH & OPEN-SOURCE FELLOWSHIPS", "research_opportunities"),
            ("OTHER RELEVANT OPPORTUNITIES", "other_opportunities"),
        ]:
            jobs = categorized_jobs.get(key, [])
            lines.append(f"[{cat_name}] ({len(jobs)} items)")
            lines.append("-" * 40)
            if not jobs:
                lines.append("No new opportunities in this category today.")
            for j in jobs:
                lines.append(f"• {j.get('title')} @ {j.get('company')}")
                lines.append(f"  Match Score: {j.get('match_score')}% | Stipend: {j.get('stipend')}")
                lines.append(f"  Location: {j.get('location')}")
                lines.append(f"  Why it matches: {j.get('match_explanation')}")
                lines.append(f"  Matched Skills: {', '.join(j.get('matched_skills', []))}")
                if j.get("missing_skills"):
                    lines.append(f"  Missing Skills to note: {', '.join(j.get('missing_skills'))}")
                lines.append(f"  Official Link: {j.get('url')}")
                lines.append("")
            lines.append("")

    lines.append("=" * 60)
    lines.append(f"Dashboard: {dash_url}")
    lines.append("Generated autonomously by Internship JARVIS via GitHub Actions.")
    return "\n".join(lines)


class EmailSender:
    """Handles email delivery via SMTP or generates local preview files."""

    def __init__(self):
        self.user = GMAIL_USER
        self.password = GMAIL_APP_PASSWORD
        self.recipient = RECIPIENT_EMAIL
        self.dry_run = DRY_RUN

    def send_report(self, categorized_jobs: Dict[str, List[Dict[str, Any]]]) -> bool:
        """Compose and deliver the email report or write preview if dry-run."""
        html_content = generate_email_html(categorized_jobs)
        text_content = generate_email_text(categorized_jobs)

        # Always save the latest HTML preview to reports/latest_report.html
        latest_file = REPORTS_DIR / "latest_report.html"
        try:
            latest_file.write_text(html_content, encoding="utf-8")
            logger.info("Saved local HTML report preview to %s", latest_file)
        except Exception as e:
            logger.warning("Could not write local report preview: %s", e)

        if self.dry_run or not (self.user and self.password):
            logger.info(
                "Running in DRY-RUN mode. Credentials not configured or DRY_RUN=true. "
                "Email delivery skipped. Local preview generated at %s",
                latest_file,
            )
            return True

        # Send live email via Gmail SMTP
        try:
            total = sum(len(v) for v in categorized_jobs.values())
            subject_summary = f"{total} New Matches" if total > 0 else "All Caught Up"
            msg = email.message.EmailMessage()
            msg["Subject"] = f"⚡ Internship JARVIS: Daily Opportunities Report - {subject_summary} ({datetime.now().strftime('%b %d')})"
            msg["From"] = f"Internship JARVIS <{self.user}>"
            msg["To"] = self.recipient

            msg.set_content(text_content)
            msg.add_alternative(html_content, subtype="html")

            logger.info("Connecting to Gmail SMTP server for %s...", self.user)
            # Use SSL on port 465
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as server:
                server.login(self.user, self.password)
                server.send_message(msg)

            logger.info("Daily internship report successfully sent to %s", self.recipient)
            return True
        except Exception as e:
            logger.error("Failed to send email via Gmail SMTP: %s", e)
            return False
