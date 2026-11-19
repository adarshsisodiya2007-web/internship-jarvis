# ⚡ Internship JARVIS

An automated, serverless Python intelligence agent and web dashboard that discovers verified tech internships matching your profile, provides an interactive dashboard, and delivers a curated daily report to your Gmail inbox every evening at **9:00 PM IST** using **GitHub Actions**.

Built specifically for early-stage Computer Science undergraduates (B.Tech CSE, Jabalpur Engineering College, 3rd semester / class of 2029) seeking software engineering, AI/ML, data science, and academic research opportunities.

---

## 🎯 Target Profile

- **Student:** B.Tech Computer Science & Engineering (Jabalpur Engineering College)
- **Academic Timeline:** Started in 2025 &bull; Expected Graduation: 2029
- **Current Academic Level:** 3rd Semester (2nd Year Undergraduate)
- **Core Skills:** Python, C, SQL, HTML, CSS, JavaScript, Git
- **Areas of Interest:** Software Development, AI/ML, Data Science, Technology Research
- **Eligibility Target:** Opportunities suitable for 1st- and 2nd-year undergraduate students (batch of 2028 / 2029)

---

## 🚀 Key Features

1. **100% Free & Accessible Data Sources:**
   - Aggregates over **5,000+ verified direct career postings** from employer portals (Greenhouse, Lever, Workday) via the SimplifyJobs public directory.
   - Live public remote & tech APIs: **Remotive API**, **Jobicy API**, **Arbeitnow API**, and **We Work Remotely RSS**.
   - Zero paid API keys, web scrapers, or third-party subscription requirements.

2. **Intelligent Match Scoring & Accurate Eligibility:**
   - Evaluates each listing on a **0–100% Match Score** using candidate skills, degree relevance, and interest alignment.
   - **Accurate eligibility checking:** Strictly flags and penalizes listings demanding graduating seniors (2025/2026), postgraduate degrees (Master's/PhD), or 3+ years of full-time experience.
   - Awards bonus points to postings specifically targeting freshman/sophomores and 2028/2029 batches.
   - Explains **why each role matches** and pinpoints **missing in-demand skills** (e.g., Docker, AWS, React, PyTorch) to guide your study roadmap.

3. **Multi-Tier Opportunity Categorization:**
   - 💰 **High-Match Paid Tech Internships:** Explicit salary/stipend or competitive corporate engineering internships.
   - 🔬 **Research & Open-Source Fellowships:** University labs, Google Summer of Code (GSoC), MLH, and academic research programs.
   - 📋 **Other Matching Opportunities:** Unpaid, credit-based, or undisclosed stipend roles.

4. **Quality & Safety Filters:**
   - **Duplicate Detection:** Generates cryptographic SHA-256 signatures for every listing and tracks them in `data/seen_jobs.json`.
   - **Spam & Scam Defense:** Rejects fee-charging listings, suspicious domains, Telegram/WhatsApp-only contact scams, and pyramid schemes.
   - **Seniority & Experience Filter:** Filters out senior, staff, lead, and 5+ years experience listings.
   - **Ethical Automation:** Strictly provides official direct career portal links; never automatically submits personal data or unauthorized applications.

5. **Interactive Web Dashboard (Flask + Render):**
   - Clean, responsive dark-mode UI with KPI cards (total scanned, total matching, paid, research, other).
   - Category filtering, eligibility alerts, skill gap chips, and direct application links.
   - **Manual Refresh button** with rate-limiting / debouncing cooldown (60s) to prevent spamming public APIs.
   - **`/health` endpoint** for Render and external uptime monitoring.
   - Zero credentials or internal logs exposed.

6. **Daily Automated Gmail Digest (GitHub Actions):**
   - Dispatched at **9:00 PM IST** (`30 15 * * *` UTC) every day.
   - Modern, mobile-responsive HTML card layout with plain-text fallback.
   - Automatically commits the latest snapshot to `data/latest_matches.json` so the dashboard stays fresh.

---

## 📂 Project Structure

```
internship-jarvis/
├── .github/
│   └── workflows/
│       └── daily.yml             # GitHub Actions workflow (9 PM IST schedule, manual dispatch & snapshot push)
├── data/
│   ├── latest_matches.json       # Snapshot of categorized matches for the web dashboard
│   └── seen_jobs.json            # Cache of previously notified jobs (duplicate prevention, gitignored)
├── reports/
│   └── latest_report.html        # Local preview of the latest generated HTML digest (gitignored)
├── src/
│   ├── __init__.py
│   ├── config.py                 # Candidate profile, skills lexicon, and environment settings
│   ├── fetcher.py                # Multi-source public API aggregator & scam detection
│   ├── matcher.py                # Match scoring engine, eligibility checker & skill gap analysis
│   ├── email_sender.py           # HTML/Plaintext template generator & Gmail SMTP dispatcher
│   ├── app.py                    # Flask web dashboard application & /health endpoint
│   └── main.py                   # Master pipeline orchestrator & CLI entry point
│   └── templates/
│       └── index.html            # Responsive dark-theme dashboard UI
├── app.py                        # Root WSGI entry point for Gunicorn / Render
├── render.yaml                   # Render Blueprint infrastructure-as-code configuration
├── .gitignore                    # Secrets, bytecode, reports, and temp files exclusion
├── requirements.txt              # Minimal lightweight dependencies (requests, python-dotenv, flask, gunicorn)
└── README.md                     # Comprehensive setup and documentation
```

---

## 🌐 Web Dashboard Deployment (Render Free Tier)

The web dashboard is fully configured for deployment as a **Free Web Service on Render** using `render.yaml` or Render's web console.

### Option A: Automatic Blueprint Deployment (Recommended)
1. Sign in to **[Render.com](https://render.com)**.
2. Click **New +** > **Blueprint**.
3. Connect your repository: `https://github.com/adarshsisodiya2007-web/internship-jarvis`.
4. Render will detect `render.yaml` and configure:
   - **Environment:** Python
   - **Plan:** Free ($0/month)
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Health Check Path:** `/health`
5. Click **Apply** to deploy!

### Option B: Manual Web Service Setup
1. In Render Dashboard, click **New +** > **Web Service**.
2. Select your repository `internship-jarvis`.
3. Set the following settings:
   - **Name:** `internship-jarvis`
   - **Region:** Any (e.g., Singapore or Oregon)
   - **Branch:** `main`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Instance Type:** `Free` (0.1 CPU, 512 MB RAM)
   - **Health Check Path:** `/health`
4. Click **Create Web Service**.

> **Note on Email & SMTP:** Render's free tier restricts outbound SMTP traffic on ports 25, 465, and 587. For this reason, email reports are handled entirely by **GitHub Actions**, while Render hosts the fast, interactive web dashboard.

---

## ⚙️ Automated Email Setup & GitHub Actions

### Step 1: Generate a Gmail App Password

1. Go to your **[Google Account Security Settings](https://myaccount.google.com/security)**.
2. Ensure **2-Step Verification** is turned **ON**.
3. Under *2-Step Verification*, scroll down to **App passwords**.
4. Enter an app name (e.g., `Internship JARVIS`) and click **Create**.
5. Copy the 16-character generated password (e.g., `abcd efgh ijkl mnop`).

---

### Step 2: Configure GitHub Secrets

In your GitHub repository (`https://github.com/adarshsisodiya2007-web/internship-jarvis`):

1. Navigate to **Settings** > **Secrets and variables** > **Actions**.
2. Click **New repository secret** and add:

| Secret Name | Description | Example Value |
| :--- | :--- | :--- |
| `GMAIL_USER` | Your full Gmail address | `yourname@gmail.com` |
| `GMAIL_APP_PASSWORD` | The 16-character Gmail App Password | `abcdefghijklmnop` |
| `RECIPIENT_EMAIL` | *(Optional)* Target inbox (defaults to `GMAIL_USER`) | `yourname@gmail.com` |

---

### Step 3: Run the Manual Workflow Test

1. Push your latest code to GitHub:
   ```bash
   git add .
   git commit -m "feat: complete dashboard, accurate eligibility matching, and Render blueprint"
   git push origin main
   ```
2. Go to the **Actions** tab on GitHub.
3. Select **Internship JARVIS Daily Run** on the left menu.
4. Click **Run workflow** > branch `main` > click **Run workflow**.
5. Confirm that the run completes, commits `data/latest_matches.json`, and delivers the email report.

---

### Step 4: Activate the 9:00 PM IST Daily Schedule

Indian Standard Time (IST) is UTC+5:30.
- **9:00 PM IST** corresponds to **15:30 UTC**.
- Cron expression: `30 15 * * *`

To activate daily automatic runs:
1. Open [`.github/workflows/daily.yml`](file:///.github/workflows/daily.yml).
2. Uncomment lines 20–21:
   ```yaml
   schedule:
     - cron: '30 15 * * *'
   ```
3. Commit and push:
   ```bash
   git add .github/workflows/daily.yml
   git commit -m "chore: enable daily 9 PM IST schedule"
   git push origin main
   ```

---

## 🧪 Local Testing

1. Run the CLI pipeline in Dry-Run mode:
   ```bash
   python -m src.main --dry-run
   ```
2. Run the local Flask web dashboard:
   ```bash
   python app.py
   ```
   Open `http://localhost:5000` in your web browser. Check `/health` at `http://localhost:5000/health`.

---

## ⚠️ Limitations of Free Public Data Sources

1. **Compensation Transparency:** Some employers list stipends as "Competitive" or "Undisclosed" until the interview or offer stage. When an explicit dollar or rupee amount is not published, JARVIS flags it as "Disclosed upon offer".
2. **Geographical & Visa Requirements:** While many positions are globally remote, certain listings may have country-specific tax or work authorization rules. Always review the eligibility section on the employer's official page before applying.
3. **Application Lifecycles:** High-demand tech internships can reach applicant caps quickly. If an application link shows "No longer accepting applications," that employer has filled their quota for the cycle.
4. **Rate Limits & API Uptime:** Free public endpoints (Remotive, Jobicy, Arbeitnow, WWR) may occasionally experience temporary network timeouts. JARVIS uses graceful error handling so if any single API is unreachable, the remaining sources continue uninterrupted.
