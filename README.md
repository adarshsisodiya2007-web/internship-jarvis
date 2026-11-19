# ⚡ Internship JARVIS

An automated, serverless Python intelligence agent that finds verified tech internships matching your specific profile and delivers a curated daily report to your Gmail inbox every evening at **9:00 PM IST** using **GitHub Actions**.

Built specifically for early-stage Computer Science undergraduates (1st & 2nd year / 3rd semester) seeking software engineering, AI/ML, data science, and academic research opportunities.

---

## 🎯 Target Profile

- **Student:** B.Tech Computer Science & Engineering (Jabalpur Engineering College)
- **Current Academic Level:** 3rd Semester (2nd Year, graduating ~2027/2028)
- **Core Skills:** Python, C, SQL, HTML, CSS, JavaScript, Git
- **Areas of Interest:** Software Development, AI/ML, Data Science, Technology Research
- **Focus:** Legitimate opportunities open to first- and second-year undergraduate students

---

## 🚀 Key Features

1. **100% Free & Accessible Data Sources:**
   - Aggregates over **5,000+ verified direct career postings** from employer portals (Greenhouse, Lever, Workday) via the SimplifyJobs public directory.
   - Live public remote & tech APIs: **Remotive API**, **Jobicy API**, **Arbeitnow API**, and **We Work Remotely RSS**.
   - Zero paid API keys, web scrapers, or third-party subscription requirements.

2. **Intelligent Match Scoring & Gap Analysis:**
   - Evaluates each listing on a **0–100% Match Score** using candidate skills, degree relevance, and interest alignment.
   - Provides a clear human-readable explanation of **why each role matches**.
   - Pinpoints **missing in-demand skills** (e.g., Docker, AWS, React, PyTorch) to highlight learning opportunities.

3. **Multi-Tier Opportunity Categorization:**
   - 💰 **High-Match Paid Tech Internships:** Explicit salary/stipend or competitive corporate engineering internships.
   - 🔬 **Research & Open-Source Fellowships:** University labs, Google Summer of Code (GSoC), MLH, and academic research programs.
   - 📋 **Other Matching Opportunities:** Unpaid, credit-based, or undisclosed stipend roles.

4. **Quality & Safety Filters:**
   - **Duplicate Detection:** Generates cryptographic SHA-256 signatures for every listing and tracks them in `data/seen_jobs.json`.
   - **Spam & Scam Defense:** Rejects fee-charging listings, suspicious domains, Telegram/WhatsApp-only contact scams, and pyramid schemes.
   - **Seniority & Experience Filter:** Filters out senior, staff, lead, and 5+ years experience listings.
   - **Ethical Automation:** Strictly provides official direct career portal links; never automatically submits personal data or unauthorized applications.

5. **Responsive Daily Email Digest:**
   - Modern, mobile-responsive HTML card layout with color-coded match badges, skill pills, eligibility notes, and direct apply buttons.
   - Clean plain-text fallback for terminal environments or text-only mail clients.

---

## 📂 Project Structure

```
nic-jarvic/
├── .github/
│   └── workflows/
│       └── daily.yml             # GitHub Actions workflow (9 PM IST schedule & manual dispatch)
├── data/
│   └── seen_jobs.json            # Cache of previously notified jobs (duplicate prevention)
├── reports/
│   └── latest_report.html        # Local preview of the latest generated HTML digest
├── src/
│   ├── __init__.py
│   ├── config.py                 # Candidate profile, skills lexicon, and environment settings
│   ├── fetcher.py                # Multi-source public API aggregator & scam detection
│   ├── matcher.py                # Match scoring engine, eligibility checker & skill gap analysis
│   ├── email_sender.py           # HTML/Plaintext template generator & Gmail SMTP dispatcher
│   └── main.py                   # Master pipeline orchestrator & CLI entry point
├── .gitignore                    # Secrets, bytecode, and temp files exclusion
├── requirements.txt              # Minimal lightweight dependencies (requests, python-dotenv)
└── README.md                     # Comprehensive setup and documentation
```

---

## ⚙️ Setup & Configuration

### Step 1: Generate a Gmail App Password

To send emails securely via Gmail without storing your Google account password:

1. Go to your **[Google Account Security Settings](https://myaccount.google.com/security)**.
2. Ensure **2-Step Verification** is turned **ON**.
3. Under *2-Step Verification*, scroll down to **App passwords** (or search "App passwords" in the top bar).
4. Enter an app name (e.g., `Internship JARVIS`) and click **Create**.
5. Copy the 16-character generated password (e.g., `abcd efgh ijkl mnop`).

---

### Step 2: Configure GitHub Secrets

In your GitHub repository:

1. Navigate to **Settings** > **Secrets and variables** > **Actions**.
2. Click **New repository secret** and add the following:

| Secret Name | Description | Example Value |
| :--- | :--- | :--- |
| `GMAIL_USER` | Your full Gmail address | `yourname@gmail.com` |
| `GMAIL_APP_PASSWORD` | The 16-character Gmail App Password | `abcdefghijklmnop` |
| `RECIPIENT_EMAIL` | *(Optional)* Target inbox (defaults to `GMAIL_USER`) | `yourname@gmail.com` |

---

### Step 3: Local Testing (Optional)

You can run Internship JARVIS locally to verify everything works:

1. Clone your repository:
   ```bash
   git clone https://github.com/<your-username>/nic-jarvic.git
   cd nic-jarvic
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. **Dry-Run Mode (No credentials required):**
   ```bash
   python -m src.main --dry-run
   ```
   *This fetches live opportunities, runs matching, and saves a formatted preview at `reports/latest_report.html` which you can open directly in any web browser!*

4. **Live Email Test (Using `.env` file):**
   Create a `.env` file in the root directory:
   ```env
   GMAIL_USER=yourname@gmail.com
   GMAIL_APP_PASSWORD=abcdefghijklmnop
   RECIPIENT_EMAIL=yourname@gmail.com
   DRY_RUN=false
   ```
   Run:
   ```bash
   python -m src.main --ignore-cache
   ```
   Check your Gmail inbox for the incoming digest!

---

### Step 4: Test GitHub Actions Manually

Before turning on the automatic schedule:

1. Push your code to GitHub:
   ```bash
   git add .
   git commit -m "feat: complete Internship JARVIS setup"
   git push origin main
   ```
2. In your GitHub repository, open the **Actions** tab.
3. Select **Internship JARVIS Daily Run** on the left menu.
4. Click **Run workflow** > select branch `main` > click the green **Run workflow** button.
5. Watch the action execute in ~30 seconds and check your Gmail inbox!

---

### Step 5: Activate the Scheduled Workflow (9:00 PM IST)

Indian Standard Time (IST) is UTC+5:30.
- **9:00 PM IST** corresponds to **15:30 UTC**.
- Cron expression: `30 15 * * *`

To activate daily automatic runs:
1. Open [`.github/workflows/daily.yml`](file:///.github/workflows/daily.yml).
2. Uncomment lines 18–19:
   ```yaml
   schedule:
     - cron: '30 15 * * *'
   ```
3. Commit and push the change:
   ```bash
   git add .github/workflows/daily.yml
   git commit -m "chore: enable daily 9 PM IST schedule"
   git push origin main
   ```
From now on, GitHub Actions will automatically scan for new internships and email your report every night at 9:00 PM IST!

---

## 🔍 Scoring Algorithm Details

Internship JARVIS calculates a comprehensive **Match Score (0–100%)**:

$$\text{Match Score} = \text{Skills (40 pts)} + \text{Interests (25 pts)} + \text{Role Level (25 pts)} + \text{Degree (10 pts)} - \text{Penalties}$$

- **Skills (Up to 40 pts):** Direct matches against candidate's core stack: Python, C, SQL, HTML, CSS, JavaScript, Git.
- **Interests (Up to 25 pts):** Keyword correlation with Software Development, AI/ML, Data Science, and Research.
- **Role Level (Up to 25 pts):** Signals specifically targeting freshmen, sophomores, 2nd-year undergrads, and 2027/2028 batch candidates.
- **Degree (Up to 10 pts):** Computer Science / B.Tech / Engineering degree alignment.
- **Deductions:** Strict penalties for roles demanding 5+ years of experience, staff/lead titles, or graduate degrees only.

---

## ⚠️ Limitations of Free Public Data Sources

While using free, open APIs and public directories enables zero-cost autonomous execution without subscription services, keep in mind:

1. **Compensation Transparency:** Some employers list stipends as "Competitive" or "Undisclosed" until the interview or offer stage. When an explicit dollar or rupee amount is not published, JARVIS flags it as "Disclosed upon offer".
2. **Geographical & Visa Requirements:** While many positions are globally remote, certain listings may have country-specific tax or work authorization rules. Always review the eligibility section on the employer's official page before applying.
3. **Application Lifecycles:** High-demand tech internships can reach applicant caps quickly. If an application link shows "No longer accepting applications," that employer has filled their quota for the cycle.
4. **Rate Limits & API Uptime:** Free public endpoints (Remotive, Jobicy, Arbeitnow) may occasionally experience temporary network hiccups. JARVIS is built with graceful error handling so if any single API is unreachable, the remaining sources continue uninterrupted.

---

## 🛡️ License & Safety

Distributed for educational and personal career automation.
**Safety Rule:** Never pay any application fee, registration fee, or security deposit for an internship. Legitimate companies never charge candidates to interview or work.
