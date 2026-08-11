# ⚡ AutoUpdate PRO — Digital Activity & Streak Controller

An all-in-one suite to automate GitHub commits, keep activity logs updated, and maintain your contribution streak effortlessly. Features a modern **Luminous Flux Light Dashboard UI**, real-time **Git log contribution heatmaps**, custom **Flaticon UI vector icons**, and a standalone **macOS App bundle** with native **Indian Standard Time (IST / Asia/Kolkata)** support.

---

## ✨ Key Features

- ☁️ **GitHub Actions Cloud Automation:** Runs 100% in the cloud without requiring local background scripts.
- 🇮🇳 **IST & Multi-Timezone Support:** Pre-configured for Indian Standard Time (`Asia/Kolkata`) with live clock and support for `UTC`, `EST`, `GMT`, `JST`, etc.
- 🎨 **Luminous Flux Light Theme:** High-contrast crisp slate-on-white design featuring Deep Sky Cyan (`#0891B2`) and Coral Orange (`#EA580C`) accents.
- 📅 **Real-Time Git Contribution Heatmap:** Parses target repository `git log` to render a 7x24 grid (5.5 months of git commits) with interactive hover tooltips and active streak counters.
- 📦 **Standalone macOS App (`AutoUpdate.app`):** Double-clickable native macOS app bundle with custom GC icon and AppKit Dock integration.
- 🖼️ **Flaticon UI Icon Set:** Clean vector icons for navigation, triggers, and configuration inputs.
- 💻 **Interactive CLI Tool (`auto_committer.py`):** Lightweight command-line utility for background automation.

---

## 🛠️ Usage Options

### Option 1: 🖥️ Standalone macOS Desktop App (`AutoUpdate.app`)

Double-clickable native macOS App with full GUI, custom Dock icon, and real-time Git Heatmap.

#### Launch:
```bash
open dist/AutoUpdate.app
```
*(Or double-click `dist/AutoUpdate.app` directly from Finder)*.

---

### Option 2: 🐍 Launch via Python (`gui_committer.py`)

Run the Python Desktop App directly from terminal:

```bash
# 1. Install dependencies
python3 -m pip install gitpython schedule customtkinter Pillow

# 2. Launch GUI App
/opt/anaconda3/bin/python3 gui_committer.py
```

#### GUI Capabilities:
- 📊 **Automation Dashboard:** Configure target Git repository, activity log file, custom commit message, and schedule frequency (Seconds, Minutes, Hours).
- 📅 **Streak Heatmap Grid:** Live GitHub-style contribution graph parsed from target repository git log.
- 📜 **Execution Console:** High-contrast real-time log terminal tracking commits, pushes, and errors.
- ⚡ **Instant Commit Trigger:** One-click instant commit and push button.
- 🇮🇳 **Live Timezone Clock:** Displays live time in selected timezone (default `Asia/Kolkata` IST).

---

### Option 3: ☁️ GitHub Actions (Cloud Automation — Zero Local Setup)

Runs automatically on GitHub servers once daily.

1. **Workflow Location:** `.github/workflows/auto-commit.yml`
2. **Default Schedule:** Daily at `00:00 IST` (Midnight Indian Standard Time) / `18:30 UTC` (`cron: '30 18 * * *'`).
3. **Manual Trigger:** Go to the **Actions** tab on your repository > Select **Auto Commit** > Click **Run workflow**.

#### 🕒 GitHub Actions Cron Converter (IST Reference):
- **00:00 IST (Midnight):** `- cron: '30 18 * * *'` (Default)
- **09:00 AM IST:** `- cron: '30 3 * * *'`
- **09:00 PM IST:** `- cron: '30 15 * * *'`

---

### Option 4: 💻 Interactive CLI Application (`auto_committer.py`)

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
├── dist/
│   └── AutoUpdate.app       # Standalone native macOS App bundle
├── .github/workflows/
│   └── auto-commit.yml     # GitHub Actions cloud automation workflow
├── assets/                  # App icons and Flaticon UI vector assets
│   ├── app_icon.icns
│   ├── app_icon.png
│   └── icon_*.png
├── gui_committer.py         # CustomTkinter Desktop GUI application
├── auto_committer.py        # Interactive CLI terminal app
├── updater.py               # Python script executed by GitHub Actions
├── activity_log.txt         # Human-readable update history log
├── data.json                # Structured JSON update metrics
├── README.md                # Project documentation
└── .gitignore               # Git ignore rules
```
