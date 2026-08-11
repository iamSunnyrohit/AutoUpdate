import os
import queue
import threading
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from git import Repo, GitCommandError
import schedule

COMMON_TIMEZONES = [
    "Asia/Kolkata (IST)",
    "UTC",
    "America/New_York (EST/EDT)",
    "America/Los_Angeles (PST/PDT)",
    "Europe/London (GMT/BST)",
    "Europe/Paris (CET/CEST)",
    "Asia/Tokyo (JST)",
    "Asia/Dubai (GST)",
    "Australia/Sydney (AEST/AEDT)",
]


def clean_tz_name(tz_display):
    return tz_display.split(" ")[0]


def get_formatted_time(tz_name="Asia/Kolkata"):
    try:
        tz = ZoneInfo(tz_name)
        now = datetime.now(tz)
        return now.strftime("%Y-%m-%d %H:%M:%S %Z (UTC%z)"), now
    except Exception:
        now = datetime.now(timezone.utc)
        return now.strftime("%Y-%m-%d %H:%M:%S UTC"), now


class AutoCommitterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub Auto-Committer Desktop App")
        self.root.geometry("840x720")
        self.root.minsize(780, 640)

        # State Variables
        self.is_running = False
        self.scheduler_thread = None
        self.stop_event = threading.Event()
        self.log_queue = queue.Queue()
        self.total_commits = 0
        self.last_commit_time = "Never"
        self.next_commit_time = "N/A"
        self.interval_val = 1
        self.unit_val = "Minutes"
        self.active_tz = "Asia/Kolkata"

        # Theme Colors (Dark Palette)
        self.bg_color = "#1e1e2e"
        self.card_bg = "#25263a"
        self.text_color = "#cdd6f4"
        self.accent_color = "#89b4fa"
        self.success_color = "#a6e3a1"
        self.error_color = "#f38ba8"
        self.warning_color = "#fab387"
        self.btn_active = "#74c7ec"

        self.root.configure(bg=self.bg_color)
        self.setup_styles()
        self.build_ui()

        self.root.after(100, self.process_log_queue)

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")

        self.style.configure(".", background=self.bg_color, foreground=self.text_color, font=("Helvetica", 10))
        self.style.configure("Card.TFrame", background=self.card_bg, relief="flat")
        self.style.configure("Header.TLabel", background=self.bg_color, foreground="#f5e0dc", font=("Helvetica", 16, "bold"))
        self.style.configure("SubHeader.TLabel", background=self.card_bg, foreground=self.accent_color, font=("Helvetica", 11, "bold"))
        self.style.configure("StatValue.TLabel", background=self.card_bg, foreground=self.success_color, font=("Helvetica", 13, "bold"))

        self.style.configure(
            "Primary.TButton",
            font=("Helvetica", 10, "bold"),
            background="#a6e3a1",
            foreground="#11111b",
            borderwidth=0,
            padding=8,
        )
        self.style.map("Primary.TButton", background=[("active", "#94e2d5")])

        self.style.configure(
            "Stop.TButton",
            font=("Helvetica", 10, "bold"),
            background="#f38ba8",
            foreground="#11111b",
            borderwidth=0,
            padding=8,
        )
        self.style.map("Stop.TButton", background=[("active", "#eba0ac")])

        self.style.configure(
            "Action.TButton",
            font=("Helvetica", 10),
            background="#89b4fa",
            foreground="#11111b",
            borderwidth=0,
            padding=8,
        )
        self.style.map("Action.TButton", background=[("active", "#74c7ec")])

    def build_ui(self):
        # Header
        header_frame = ttk.Frame(self.root, padding=(20, 15, 20, 10))
        header_frame.pack(fill="x")

        title_lbl = ttk.Label(header_frame, text="⚡ GitHub Auto-Committer Desktop", style="Header.TLabel")
        title_lbl.pack(side="left")

        self.status_badge = tk.Label(
            header_frame,
            text="STATUS: STOPPED",
            bg=self.error_color,
            fg="#11111b",
            font=("Helvetica", 10, "bold"),
            padx=10,
            pady=4,
        )
        self.status_badge.pack(side="right")

        # Configuration Card
        config_card = ttk.Frame(self.root, style="Card.TFrame", padding=15)
        config_card.pack(fill="x", padx=20, pady=5)

        ttk.Label(config_card, text="Repository & Timezone Configuration", style="SubHeader.TLabel").grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))

        # Repo Path
        ttk.Label(config_card, text="Repository Path:", background=self.card_bg).grid(row=1, column=0, sticky="w", pady=4)
        self.repo_entry = tk.Entry(config_card, bg="#313244", fg=self.text_color, insertbackground="white", relief="flat", font=("Helvetica", 10))
        self.repo_entry.insert(0, os.getcwd())
        self.repo_entry.grid(row=1, column=1, sticky="ew", padx=8, pady=4)

        browse_btn = tk.Button(
            config_card,
            text="Browse...",
            command=self.browse_repo,
            bg="#45475a",
            fg=self.text_color,
            activebackground="#585b70",
            activeforeground=self.text_color,
            relief="flat",
            font=("Helvetica", 9),
        )
        browse_btn.grid(row=1, column=2, sticky="e", pady=4)

        # Timezone Selection
        ttk.Label(config_card, text="Target Timezone:", background=self.card_bg).grid(row=2, column=0, sticky="w", pady=4)
        self.tz_combo = ttk.Combobox(config_card, values=COMMON_TIMEZONES, state="readonly", font=("Helvetica", 10))
        self.tz_combo.set("Asia/Kolkata (IST)")
        self.tz_combo.grid(row=2, column=1, columnspan=2, sticky="ew", padx=8, pady=4)

        # Target File
        ttk.Label(config_card, text="Target Log File:", background=self.card_bg).grid(row=3, column=0, sticky="w", pady=4)
        self.target_file_entry = tk.Entry(config_card, bg="#313244", fg=self.text_color, insertbackground="white", relief="flat", font=("Helvetica", 10))
        self.target_file_entry.insert(0, "activity_log.txt")
        self.target_file_entry.grid(row=3, column=1, columnspan=2, sticky="ew", padx=8, pady=4)

        # Custom Commit Message
        ttk.Label(config_card, text="Commit Message:", background=self.card_bg).grid(row=4, column=0, sticky="w", pady=4)
        self.msg_entry = tk.Entry(config_card, bg="#313244", fg=self.text_color, insertbackground="white", relief="flat", font=("Helvetica", 10))
        self.msg_entry.insert(0, "chore: automated activity update")
        self.msg_entry.grid(row=4, column=1, columnspan=2, sticky="ew", padx=8, pady=4)

        # Schedule Settings
        ttk.Label(config_card, text="Interval Frequency:", background=self.card_bg).grid(row=5, column=0, sticky="w", pady=4)

        freq_frame = ttk.Frame(config_card, style="Card.TFrame")
        freq_frame.grid(row=5, column=1, columnspan=2, sticky="w", padx=8, pady=4)

        self.interval_entry = tk.Entry(freq_frame, width=8, bg="#313244", fg=self.text_color, insertbackground="white", relief="flat", font=("Helvetica", 10))
        self.interval_entry.insert(0, "1")
        self.interval_entry.pack(side="left", padx=(0, 10))

        self.unit_combo = ttk.Combobox(freq_frame, values=["Seconds", "Minutes", "Hours"], width=10, state="readonly")
        self.unit_combo.set("Minutes")
        self.unit_combo.pack(side="left")

        config_card.columnconfigure(1, weight=1)

        # Action Controls Card
        ctrl_card = ttk.Frame(self.root, style="Card.TFrame", padding=15)
        ctrl_card.pack(fill="x", padx=20, pady=10)

        self.start_btn = ttk.Button(ctrl_card, text="▶ Start Auto-Committer", style="Primary.TButton", command=self.start_scheduler)
        self.start_btn.pack(side="left", padx=(0, 10))

        self.stop_btn = ttk.Button(ctrl_card, text="⏹ Stop", style="Stop.TButton", command=self.stop_scheduler, state="disabled")
        self.stop_btn.pack(side="left", padx=(0, 10))

        self.now_btn = ttk.Button(ctrl_card, text="⚡ Commit & Push Now", style="Action.TButton", command=self.commit_now)
        self.now_btn.pack(side="left")

        clear_btn = tk.Button(
            ctrl_card,
            text="Clear Logs",
            command=self.clear_logs,
            bg="#45475a",
            fg=self.text_color,
            activebackground="#585b70",
            relief="flat",
            font=("Helvetica", 9),
        )
        clear_btn.pack(side="right")

        # Stats Cards Panel
        stats_frame = ttk.Frame(self.root, padding=(20, 0, 20, 5))
        stats_frame.pack(fill="x")

        s1 = ttk.Frame(stats_frame, style="Card.TFrame", padding=10)
        s1.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Label(s1, text="Total Commits", background=self.card_bg, font=("Helvetica", 9)).pack()
        self.stat_commits_lbl = ttk.Label(s1, text="0", style="StatValue.TLabel")
        self.stat_commits_lbl.pack()

        s2 = ttk.Frame(stats_frame, style="Card.TFrame", padding=10)
        s2.pack(side="left", fill="x", expand=True, padx=5)
        ttk.Label(s2, text="Last Commit", background=self.card_bg, font=("Helvetica", 9)).pack()
        self.stat_last_lbl = ttk.Label(s2, text="Never", style="StatValue.TLabel")
        self.stat_last_lbl.pack()

        s3 = ttk.Frame(stats_frame, style="Card.TFrame", padding=10)
        s3.pack(side="left", fill="x", expand=True, padx=(5, 0))
        ttk.Label(s3, text="Next Run", background=self.card_bg, font=("Helvetica", 9)).pack()
        self.stat_next_lbl = ttk.Label(s3, text="N/A", style="StatValue.TLabel")
        self.stat_next_lbl.pack()

        # Console Log View
        log_frame = ttk.Frame(self.root, padding=(20, 10, 20, 20))
        log_frame.pack(fill="both", expand=True)

        ttk.Label(log_frame, text="Real-time Execution Output", style="Header.TLabel", font=("Helvetica", 11, "bold")).pack(anchor="w", pady=(0, 5))

        self.log_text = ScrolledText(
            log_frame,
            bg="#11111b",
            fg=self.text_color,
            insertbackground="white",
            relief="flat",
            font=("Menlo", 10),
            wrap="word",
        )
        self.log_text.pack(fill="both", expand=True)

        self.log_text.tag_config("SUCCESS", foreground=self.success_color)
        self.log_text.tag_config("ERROR", foreground=self.error_color)
        self.log_text.tag_config("INFO", foreground=self.accent_color)
        self.log_text.tag_config("WARN", foreground=self.warning_color)

        self.log("INFO", "Application ready. Configured by default for Indian Standard Time (IST / Asia/Kolkata).")

    def browse_repo(self):
        selected_dir = filedialog.askdirectory(initialdir=self.repo_entry.get())
        if selected_dir:
            self.repo_entry.delete(0, tk.END)
            self.repo_entry.insert(0, selected_dir)

    def log(self, tag, message):
        tz_name = clean_tz_name(self.tz_combo.get())
        timestamp_str, _ = get_formatted_time(tz_name)
        formatted = f"[{timestamp_str}] [{tag}] {message}\n"
        self.log_queue.put((tag, formatted))

    def process_log_queue(self):
        while not self.log_queue.empty():
            tag, msg = self.log_queue.get()
            self.log_text.insert(tk.END, msg, tag)
            self.log_text.see(tk.END)
        self.root.after(100, self.process_log_queue)

    def clear_logs(self):
        self.log_text.delete("1.0", tk.END)

    def update_next_run_time(self):
        if not self.is_running:
            self.stat_next_lbl.config(text="N/A")
            return

        tz_name = clean_tz_name(self.tz_combo.get())
        _, now_tz = get_formatted_time(tz_name)

        if self.unit_val == "Seconds":
            next_t = now_tz + timedelta(seconds=self.interval_val)
        elif self.unit_val == "Hours":
            next_t = now_tz + timedelta(hours=self.interval_val)
        else:
            next_t = now_tz + timedelta(minutes=self.interval_val)

        self.next_commit_time = next_t.strftime("%H:%M:%S")
        self.stat_next_lbl.config(text=self.next_commit_time)

    def perform_git_commit(self, is_manual=False):
        repo_path = self.repo_entry.get().strip()
        target_file = self.target_file_entry.get().strip() or "activity_log.txt"
        commit_msg = self.msg_entry.get().strip() or "chore: automated activity update"
        tz_name = clean_tz_name(self.tz_combo.get())

        if not os.path.exists(repo_path):
            self.log("ERROR", f"Repository directory non-existent: {repo_path}")
            return False

        file_path = os.path.join(repo_path, target_file)
        timestamp_str, now_tz = get_formatted_time(tz_name)

        try:
            # 1. Update target file
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(f"Updated at: {timestamp_str}\n")

            # 2. Stage changes
            repo = Repo(repo_path)
            repo.git.add(target_file)

            # 3. Commit
            full_msg = f"{commit_msg} [{timestamp_str}]"
            repo.index.commit(full_msg)

            # 4. Push
            origin = repo.remote(name="origin")
            origin.push()

            self.total_commits += 1
            self.last_commit_time = now_tz.strftime("%H:%M:%S")

            self.root.after(0, lambda: self.stat_commits_lbl.config(text=str(self.total_commits)))
            self.root.after(0, lambda: self.stat_last_lbl.config(text=self.last_commit_time))

            prefix = "Manual" if is_manual else "Scheduled"
            self.log("SUCCESS", f"{prefix} commit & push successful: '{full_msg}'")
            return True

        except GitCommandError as e:
            self.log("ERROR", f"Git error: {e}")
            return False
        except Exception as e:
            self.log("ERROR", f"Execution error: {e}")
            return False

    def commit_now(self):
        self.log("INFO", "Triggering instant manual commit...")
        threading.Thread(target=self.perform_git_commit, args=(True,), daemon=True).start()

    def start_scheduler(self):
        try:
            self.interval_val = float(self.interval_entry.get().strip())
            if self.interval_val <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input", "Interval must be a positive number.")
            return

        self.unit_val = self.unit_combo.get()
        self.is_running = True
        self.stop_event.clear()

        self.status_badge.config(text="STATUS: RUNNING", bg=self.success_color)
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.repo_entry.config(state="disabled")
        self.interval_entry.config(state="disabled")
        self.tz_combo.config(state="disabled")

        tz_name = clean_tz_name(self.tz_combo.get())
        self.log("INFO", f"Auto-committer started. Running every {self.interval_val} {self.unit_val} [{tz_name}].")

        self.log("INFO", "Performing initial start-up commit...")
        threading.Thread(target=self.perform_git_commit, daemon=True).start()
        self.update_next_run_time()

        self.scheduler_thread = threading.Thread(target=self.run_schedule_loop, daemon=True)
        self.scheduler_thread.start()

    def run_schedule_loop(self):
        schedule.clear()

        if self.unit_val == "Seconds":
            schedule.every(self.interval_val).seconds.do(self.perform_git_commit)
        elif self.unit_val == "Hours":
            schedule.every(self.interval_val).hours.do(self.perform_git_commit)
        else:
            schedule.every(self.interval_val).minutes.do(self.perform_git_commit)

        while not self.stop_event.is_set():
            schedule.run_pending()
            time.sleep(1)

    def stop_scheduler(self):
        self.is_running = False
        self.stop_event.set()
        schedule.clear()

        self.status_badge.config(text="STATUS: STOPPED", bg=self.error_color)
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.repo_entry.config(state="normal")
        self.interval_entry.config(state="normal")
        self.tz_combo.config(state="readonly")

        self.stat_next_lbl.config(text="N/A")
        self.log("WARN", "Auto-committer schedule stopped by user.")


def main():
    root = tk.Tk()
    app = AutoCommitterGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
