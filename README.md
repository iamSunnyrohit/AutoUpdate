# ⚡ AutoUpdate — Automated GitHub Activity & Commit Manager

An all-in-one suite to automate GitHub commits, keep activity logs up to date, and maintain your contribution streak effortlessly. Works seamlessly both **in the cloud (GitHub Actions)** and **locally (Desktop GUI & CLI apps)** with native **Indian Standard Time (IST / Asia/Kolkata)** and multi-timezone support.

---

## ✨ Key Features

- ☁️ **GitHub Actions Cloud Automation:** Runs 100% in the cloud without requiring local background scripts.
- 🇮🇳 **IST & Multi-Timezone Support:** Pre-configured for Indian Standard Time (`Asia/Kolkata`) with full support for `UTC`, `EST`, `GMT`, `JST`, etc.
- 🖥️ **Modern Desktop GUI App (`gui_committer.py`):** Interactive Tkinter desktop panel with real-time logs, stats dashboard, instant manual triggers, and custom schedules.
- 💻 **Interactive CLI Tool (`auto_committer.py`):** Command-line utility for quick local background automation.
- 📊 **Structured History & Logs:** Maintains both readable log lines (`activity_log.txt`) and JSON statistics history (`data.json`).

---

## 🛠️ Usage Options

### Option 1: ☁️ GitHub Actions (Cloud Automation — Zero Local Setup)

Runs automatically on GitHub servers once daily.

1. **Workflow Location:** `.github/workflows/auto-commit.yml`
2. **Default Schedule:** Daily at `00:00 IST` (Midnight Indian Standard Time) / `18:30 UTC` (`cron: '30 18 * * *'`).
3. **Manual Trigger:** Go to the **Actions** tab on your repository > Select **Auto Commit** > Click **Run workflow**.

#### 🕒 GitHub Actions Cron Converter (IST Reference):
- **00:00 IST (Midnight):** `- cron: '30 18 * * *'` (Default)
- **09:00 AM IST:** `- cron: '30 3 * * *'`
- **09:00 PM IST:** `- cron: '30 15 * * *'`

---

### Option 2: 🖥️ Desktop GUI Application (`gui_committer.py`)

A desktop control panel with background threading, visual status indicators, real-time log terminal, and timezone selection.

#### Installation & Launch:
```bash
# 1. Install dependencies
pip install gitpython schedule

# 2. Launch Desktop GUI App
python3 gui_committer.py
```

#### GUI Capabilities:
- 📁 **Repository Browser:** Select any local Git repository directory.
- 🌏 **Timezone Selector:** Choose between `Asia/Kolkata (IST)`, `UTC`, `America/New_York (EST)`, `Europe/London (GMT)`, etc.
- ⏱️ **Custom Intervals:** Schedule runs in **Seconds**, **Minutes**, or **Hours**.
- 💬 **Custom Commit Messages:** Modify commit message on the fly.
- ⚡ **Instant Commit Button:** Perform instant manual commit and push anytime.
- 📊 **Session Statistics:** Live counter for Total Commits, Last Commit Time, and Next Run Time.

---

### Option 3: 💻 Interactive CLI Application (`auto_committer.py`)

Lightweight interactive terminal application.

#### Launch:
```bash
python3 auto_committer.py
```
1. Select your target timezone (IST, UTC, or custom).
2. Enter commit message and schedule interval.
3. Performs an immediate initial commit and runs continuously in the terminal until stopped with `Ctrl + C`.

---

## ⚙️ Required GitHub Repository Settings

To ensure GitHub Actions can commit and push back to your repository:

1. **Enable Write Permissions:**
   - Go to your repository **Settings** on GitHub.
   - Navigate to **Actions** -> **General**.
   - Under **Workflow permissions**, select **Read and write permissions**.
   - Click **Save**.

2. **Show Private Contributions (Optional for Private Repositories):**
   - Go to your [GitHub Profile](https://github.com).
   - Click **Contribution settings** above the contribution graph.
   - Check **Private contributions**.

---

## 📁 Repository File Structure

```text
AutoUpdate/
├── .github/workflows/
│   └── auto-commit.yml     # GitHub Actions cloud automation workflow
├── updater.py               # Python script executed by GitHub Actions
├── gui_committer.py         # Tkinter Desktop GUI application
├── auto_committer.py        # Interactive CLI terminal app
├── activity_log.txt         # Human-readable update history log
├── data.json                # Structured JSON update metrics
├── README.md                # Project documentation
└── .gitignore               # Git ignore rules
```
