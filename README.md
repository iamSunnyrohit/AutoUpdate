# AutoUpdate - GitHub Activity Automation Tools

This repository contains multi-platform tools to automate and manage GitHub commits:

---

## 1. ☁️ GitHub Actions Workflow (Cloud Automation)
Runs on GitHub servers automatically without requiring local scripts or background processes.

- **Workflow File:** `.github/workflows/auto-commit.yml`
- **Schedule:** Runs daily at `00:00 UTC` (or via manual `workflow_dispatch`).
- **Python Script:** `updater.py` (updates log history, timestamping, and stats).

---

## 2. 🖥️ Desktop GUI App (Tkinter)
A modern desktop app with continuous scheduling, real-time logs, stats dashboard, and direct "Commit & Push Now" controls.

### How to Run:
```bash
pip install gitpython schedule
python3 gui_committer.py
```

### Features:
- 📁 **Repository & Target File Selector** (Browse any local Git folder)
- ⏱️ **Custom Schedule Frequencies** (Seconds, Minutes, Hours)
- 💬 **Custom Commit Messages**
- ⚡ **Instant Manual Commit & Push Button**
- 📊 **Real-time Stats Dashboard** (Total Commits, Last Commit Time, Next Run)
- 📝 **Live Console Output Window** (Color-coded execution output)

---

## 3. 💻 Interactive CLI App (`auto_committer.py`)
A lightweight, command-line interface for local background automation.

### How to Run:
```bash
pip install gitpython schedule
python3 auto_committer.py
```
- Enter commit message, interval unit, and frequency when prompted.
- Runs continuously in the background until stopped with `Ctrl + C`.
