# 🤖 AI Job Agent — Setup Guide

Every morning at 7 AM, this agent scrapes LinkedIn for fresh jobs, rewrites your resume
for each role using GPT-4o, saves tailored `.docx` files, and emails you a digest.
**Runs 100% locally — no n8n, no Apify, no cloud subscriptions needed.**

---

## What You Need From Your End

### 1. 🔑 OpenAI API Key
- Go to: https://platform.openai.com/api-keys
- Click **"Create new secret key"**
- Copy the key (starts with `sk-...`)
- **Estimated cost:** ~$0.05–0.15 per daily run (5 jobs × GPT-4o)

### 2. 📄 Your Resume as a PDF
- Export your resume to PDF format
- Place it in the `ai_job_agent/` folder
- Note the filename (default: `resume.pdf`)

### 3. 📧 Gmail App Password
> This is NOT your regular Gmail login password. It's a special 16-char password.

Steps:
1. Go to your Google Account → **Security**
2. Enable **2-Step Verification** (if not already on)
3. Search for **"App Passwords"** in Google Account settings
4. Create a new App Password → Select "Mail" → Select "Windows Computer"
5. Copy the 16-character password shown (looks like: `xxxx xxxx xxxx xxxx`)

---

## Setup Steps

### Step 1 — Install Python
Make sure you have Python 3.9+ installed:
```
python --version
```
Download from: https://python.org if needed.

### Step 2 — Install dependencies
Open a terminal in the `ai_job_agent/` folder and run:
```
pip install -r requirements.txt
```

### Step 3 — Create your .env file
Copy the example file:
```
cp .env.example .env
```

Then open `.env` and fill in:
```
JOB_SEARCH_QUERY=AI Product Manager        ← Your target role
JOB_SEARCH_LOCATION=United States          ← Your preferred location
JOB_MAX_RESULTS=5                          ← Jobs per day (5 recommended)
JOB_HOURS_OLD=24                           ← Only jobs posted in last 24h

RESUME_PDF_PATH=resume.pdf                 ← Your resume filename

OPENAI_API_KEY=sk-...your-key...           ← From Step 1 above
OPENAI_MODEL=gpt-4o                        ← Keep as-is

EMAIL_SENDER=your.email@gmail.com          ← Your Gmail address
EMAIL_PASSWORD=xxxx xxxx xxxx xxxx        ← Gmail App Password (Step 3 above)
EMAIL_RECIPIENT=your.email@gmail.com       ← Where to send the digest

SCHEDULE_HOUR=7                            ← Run at 7 AM
SCHEDULE_MINUTE=0
```

### Step 4 — Test it manually (first run)
Before scheduling, run it once to make sure everything works:
```
python main.py
```

You should see the agent scrape jobs, rewrite resumes, save .docx files, and send an email.

### Step 5 — Set up daily scheduling

**Option A: Run the built-in scheduler (simplest)**
Keep this running in a terminal:
```
python scheduler.py
```
The agent will wake up every day at 7 AM automatically.

**Option B: Windows Task Scheduler (runs even if terminal is closed)**
1. Open Task Scheduler → Create Basic Task
2. Name: "AI Job Agent"
3. Trigger: Daily at 7:00 AM
4. Action: Start a program → `python`
5. Arguments: `main.py`
6. Start in: `C:\path\to\ai_job_agent\`

**Option C: Mac/Linux cron (runs even if terminal is closed)**
Run `crontab -e` and add:
```
0 7 * * * cd /path/to/ai_job_agent && python main.py >> agent.log 2>&1
```

---

## File Structure
```
ai_job_agent/
├── .env                  ← Your secrets (never share this!)
├── .env.example          ← Template
├── config.py             ← All settings
├── main.py               ← Run manually: python main.py
├── scheduler.py          ← Run for daily automation: python scheduler.py
├── scraper.py            ← LinkedIn job scraper
├── resume_reader.py      ← PDF reader
├── ai_rewriter.py        ← GPT-4o resume tailoring
├── docx_writer.py        ← Saves tailored resumes as .docx
├── emailer.py            ← Gmail digest sender
├── requirements.txt      ← Python packages
├── resume.pdf            ← YOUR RESUME (place here)
├── tailored_resumes/     ← Generated .docx files (auto-created)
└── agent.log             ← Run history log (auto-created)
```

---

## Troubleshooting

**"No jobs found"**
→ Try broadening `JOB_SEARCH_QUERY` (e.g., "Product Manager" instead of "AI Product Manager")
→ Increase `JOB_HOURS_OLD` to 48 or 72

**"Gmail authentication failed"**
→ You must use an App Password, not your Gmail login password
→ Make sure 2-Step Verification is enabled first

**"Resume PDF could not be extracted"**
→ Your PDF may be image-only (scanned). Export it fresh from Word/Google Docs as a text-based PDF.

**LinkedIn blocking scraping**
→ Try running less frequently (set `JOB_HOURS_OLD=48` and run every 2 days)
→ Add a VPN if you're getting blocked frequently

---

## Resources Needed From You (Summary)

| Resource | Where to Get It | Cost |
|----------|----------------|------|
| OpenAI API Key | platform.openai.com/api-keys | ~$0.05–0.15/day |
| Gmail App Password | myaccount.google.com/apppasswords | Free |
| Your Resume (PDF) | Export from Word/Google Docs | Free |
| Python 3.9+ | python.org | Free |

That's it. No cloud subscriptions, no n8n, no Apify.
