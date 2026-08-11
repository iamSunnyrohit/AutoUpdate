import json
import os
import queue
import random
import threading
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# Fix macOS Tk 8.6 NSApplication macOSVersion crash
try:
    from AppKit import NSApplication
    def _macOSVersion(self):
        return (14, 0, 0)
    if not hasattr(NSApplication, "macOSVersion"):
        NSApplication.macOSVersion = _macOSVersion
except Exception:
    pass

import customtkinter as ctk
from git import Repo, GitCommandError
from PIL import Image, ImageTk
import schedule

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

# CustomTkinter Configuration
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

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

PRESET_MESSAGES = [
    "chore: automated activity update",
    "feat: daily ping & contribution sync",
    "docs: log status snapshot",
    "ci: automated streak update",
    "style: daily log maintenance",
]


def set_macos_dock_icon():
    """Sets native macOS Dock icon via AppKit if available."""
    try:
        from AppKit import NSApplication, NSImage
        app_icon_path = os.path.join(ASSETS_DIR, "app_icon.png")
        if os.path.exists(app_icon_path):
            ns_app = NSApplication.sharedApplication()
            ns_img = NSImage.alloc().initWithContentsOfFile_(app_icon_path)
            if ns_app and ns_img:
                ns_app.setApplicationIconImage_(ns_img)
    except Exception:
        pass


def load_flaticon_image(icon_filename, size=(20, 20)):
    path = os.path.join(ASSETS_DIR, icon_filename)
    if os.path.exists(path):
        try:
            pil_img = Image.open(path)
            return ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
        except Exception:
            return None
    return None


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


class ModernAutoCommitterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AutoUpdate Pro — Mixwellx Modern Dashboard")
        self.geometry("1120x780")
        self.minsize(980, 680)

        # Set Window Icon
        app_icon_path = os.path.join(ASSETS_DIR, "app_icon.png")
        if os.path.exists(app_icon_path):
            try:
                icon_img = Image.open(app_icon_path)
                self._photo_icon = ImageTk.PhotoImage(icon_img)
                self.wm_iconphoto(True, self._photo_icon)
            except Exception:
                pass

        # Set macOS Dock Icon asynchronously after window creation
        self.after(300, set_macos_dock_icon)

        # State Variables
        self.is_running = False
        self.scheduler_thread = None
        self.stop_event = threading.Event()
        self.log_queue = queue.Queue()

        self.total_commits = 0
        self.streak_days = 0
        self.last_commit_str = "Never"
        self.next_commit_str = "N/A"
        self.interval_val = 1
        self.unit_val = "Minutes"
        self.active_tz = "Asia/Kolkata"

        # Theme Colors (Mixwellx Modern Dark Palette)
        self.bg_main = "#0a0c16"
        self.bg_sidebar = "#111425"
        self.card_bg = "#181c33"
        self.card_border = "#252b4a"
        self.accent_indigo = "#6366f1"
        self.accent_purple = "#8b5cf6"
        self.accent_cyan = "#06b6d4"
        self.accent_emerald = "#10b981"
        self.accent_rose = "#f43f5e"
        self.text_primary = "#f8fafc"
        self.text_secondary = "#94a3b8"

        self.configure(fg_color=self.bg_main)

        # Preload Flaticon UI Icons
        self.img_bolt = load_flaticon_image("icon_bolt.png", size=(24, 24))
        self.img_dash = load_flaticon_image("icon_dashboard.png", size=(18, 18))
        self.img_heatmap = load_flaticon_image("icon_heatmap.png", size=(18, 18))
        self.img_logs = load_flaticon_image("icon_logs.png", size=(18, 18))
        self.img_folder = load_flaticon_image("icon_folder.png", size=(16, 16))
        self.img_clock = load_flaticon_image("icon_clock.png", size=(16, 16))
        self.img_play = load_flaticon_image("icon_play.png", size=(18, 18))
        self.img_stop = load_flaticon_image("icon_stop.png", size=(18, 18))
        self.img_push = load_flaticon_image("icon_push.png", size=(18, 18))

        self.setup_grid_layout()
        self.build_sidebar()
        self.build_main_header()
        self.build_stats_cards()
        self.build_tabbed_workspace()

        # Start Async Polling & Initial Git Heatmap Render
        self.after(100, self.process_log_queue)
        self.after(1000, self.update_live_clock)
        self.after(500, self.fetch_and_render_git_heatmap)

        self.log("INFO", "AutoUpdate Pro initialized. Git Heatmap active & connected to repository history.")

    def setup_grid_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, fg_color=self.bg_sidebar, width=230, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(7, weight=1)

        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.pack(padx=20, pady=(25, 20), anchor="w")

        if self.img_bolt:
            brand_icon = ctk.CTkLabel(brand_frame, image=self.img_bolt, text="")
        else:
            brand_icon = ctk.CTkLabel(brand_frame, text="⚡", font=("SF Pro Display", 24))
        brand_icon.pack(side="left", padx=(0, 10))

        brand_title = ctk.CTkLabel(brand_frame, text="AutoUpdate", font=("SF Pro Display", 18, "bold"), text_color=self.text_primary)
        brand_title.pack(side="left")

        pro_badge = ctk.CTkLabel(brand_frame, text=" PRO", font=("SF Pro Display", 10, "bold"), text_color=self.accent_indigo)
        pro_badge.pack(side="left")

        self.sidebar_status_badge = ctk.CTkLabel(
            self.sidebar,
            text="● SYSTEM STOPPED",
            font=("SF Pro Display", 11, "bold"),
            text_color=self.accent_rose,
            fg_color="#2b1725",
            corner_radius=12,
            padx=12,
            pady=4,
        )
        self.sidebar_status_badge.pack(padx=20, pady=(0, 20), anchor="w")

        ctk.CTkFrame(self.sidebar, height=1, fg_color=self.card_border).pack(fill="x", padx=15, pady=(0, 15))

        self.nav_btn_dash = ctk.CTkButton(
            self.sidebar,
            text="  Dashboard",
            image=self.img_dash,
            compound="left",
            font=("SF Pro Text", 13, "bold"),
            fg_color=self.accent_indigo,
            text_color="#ffffff",
            hover_color="#4f46e5",
            anchor="w",
            corner_radius=8,
            height=40,
            command=lambda: self.switch_tab("dash"),
        )
        self.nav_btn_dash.pack(fill="x", padx=15, pady=4)

        self.nav_btn_heatmap = ctk.CTkButton(
            self.sidebar,
            text="  Streak Heatmap",
            image=self.img_heatmap,
            compound="left",
            font=("SF Pro Text", 13),
            fg_color="transparent",
            text_color=self.text_secondary,
            hover_color=self.card_bg,
            anchor="w",
            corner_radius=8,
            height=40,
            command=lambda: self.switch_tab("heatmap"),
        )
        self.nav_btn_heatmap.pack(fill="x", padx=15, pady=4)

        self.nav_btn_logs = ctk.CTkButton(
            self.sidebar,
            text="  Real-time Logs",
            image=self.img_logs,
            compound="left",
            font=("SF Pro Text", 13),
            fg_color="transparent",
            text_color=self.text_secondary,
            hover_color=self.card_bg,
            anchor="w",
            corner_radius=8,
            height=40,
            command=lambda: self.switch_tab("logs"),
        )
        self.nav_btn_logs.pack(fill="x", padx=15, pady=4)

        tz_card = ctk.CTkFrame(self.sidebar, fg_color=self.card_bg, corner_radius=12, border_width=1, border_color=self.card_border)
        tz_card.pack(side="bottom", fill="x", padx=15, pady=20)

        tz_header = ctk.CTkFrame(tz_card, fg_color="transparent")
        tz_header.pack(padx=12, pady=(10, 2), anchor="w")

        if self.img_clock:
            ctk.CTkLabel(tz_header, image=self.img_clock, text="").pack(side="left", padx=(0, 6))
        ctk.CTkLabel(tz_header, text="LIVE TIME (IST)", font=("SF Pro Text", 10, "bold"), text_color=self.accent_cyan).pack(side="left")

        self.clock_lbl = ctk.CTkLabel(tz_card, text="00:00:00 IST", font=("SF Pro Display", 14, "bold"), text_color=self.text_primary)
        self.clock_lbl.pack(padx=12, pady=(0, 10), anchor="w")

    def build_main_header(self):
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=25, pady=20)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(3, weight=1)

        header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))

        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(title_box, text="Digital Activity & Streak Controller", font=("SF Pro Display", 22, "bold"), text_color=self.text_primary).pack(anchor="w")
        ctk.CTkLabel(title_box, text="Automate GitHub activity, monitor contribution trends, and schedule triggers.", font=("SF Pro Text", 12), text_color=self.text_secondary).pack(anchor="w")

        self.quick_commit_btn = ctk.CTkButton(
            header_frame,
            text=" Commit & Push Now",
            image=self.img_push,
            compound="left",
            font=("SF Pro Text", 12, "bold"),
            fg_color=self.accent_purple,
            hover_color="#7c3aed",
            height=38,
            corner_radius=8,
            command=self.commit_now,
        )
        self.quick_commit_btn.pack(side="right", padx=(10, 0))

    def build_stats_cards(self):
        stats_container = ctk.CTkFrame(self.main_container, fg_color="transparent")
        stats_container.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        stats_container.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="stat_cards")

        # Card 1: Total Commits
        c1 = ctk.CTkFrame(stats_container, fg_color=self.card_bg, corner_radius=12, border_width=1, border_color=self.card_border)
        c1.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkLabel(c1, text="Total Commits", font=("SF Pro Text", 11), text_color=self.text_secondary).pack(padx=15, pady=(12, 2), anchor="w")
        self.card1_val = ctk.CTkLabel(c1, text="0", font=("SF Pro Display", 22, "bold"), text_color=self.accent_emerald)
        self.card1_val.pack(padx=15, pady=(0, 12), anchor="w")

        # Card 2: Active Streak
        c2 = ctk.CTkFrame(stats_container, fg_color=self.card_bg, corner_radius=12, border_width=1, border_color=self.card_border)
        c2.grid(row=0, column=1, sticky="ew", padx=4)
        ctk.CTkLabel(c2, text="Active Streak", font=("SF Pro Text", 11), text_color=self.text_secondary).pack(padx=15, pady=(12, 2), anchor="w")
        self.card2_val = ctk.CTkLabel(c2, text="🔥 0 Days", font=("SF Pro Display", 22, "bold"), text_color=self.accent_indigo)
        self.card2_val.pack(padx=15, pady=(0, 12), anchor="w")

        # Card 3: Last Commit Time
        c3 = ctk.CTkFrame(stats_container, fg_color=self.card_bg, corner_radius=12, border_width=1, border_color=self.card_border)
        c3.grid(row=0, column=2, sticky="ew", padx=4)
        ctk.CTkLabel(c3, text="Last Execution", font=("SF Pro Text", 11), text_color=self.text_secondary).pack(padx=15, pady=(12, 2), anchor="w")
        self.card3_val = ctk.CTkLabel(c3, text="Never", font=("SF Pro Display", 15, "bold"), text_color=self.text_primary)
        self.card3_val.pack(padx=15, pady=(4, 12), anchor="w")

        # Card 4: Next Scheduled Run
        c4 = ctk.CTkFrame(stats_container, fg_color=self.card_bg, corner_radius=12, border_width=1, border_color=self.card_border)
        c4.grid(row=0, column=3, sticky="ew", padx=(8, 0))
        ctk.CTkLabel(c4, text="Next Run", font=("SF Pro Text", 11), text_color=self.text_secondary).pack(padx=15, pady=(12, 2), anchor="w")
        self.card4_val = ctk.CTkLabel(c4, text="N/A", font=("SF Pro Display", 15, "bold"), text_color=self.accent_cyan)
        self.card4_val.pack(padx=15, pady=(4, 12), anchor="w")

    def build_tabbed_workspace(self):
        self.tabview = ctk.CTkTabview(
            self.main_container,
            fg_color=self.card_bg,
            segmented_button_fg_color=self.bg_sidebar,
            segmented_button_selected_color=self.accent_indigo,
            segmented_button_selected_hover_color="#4f46e5",
            corner_radius=14,
        )
        self.tabview.grid(row=3, column=0, sticky="nsew")

        self.tab_dash = self.tabview.add("Automation Dashboard")
        self.tab_heatmap = self.tabview.add("Contribution Heatmap")
        self.tab_logs = self.tabview.add("Execution Console")

        self.build_dashboard_tab()
        self.build_heatmap_tab()
        self.build_logs_tab()

    def build_dashboard_tab(self):
        self.tab_dash.columnconfigure((0, 1), weight=1)

        cfg_frame = ctk.CTkFrame(self.tab_dash, fg_color="transparent")
        cfg_frame.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)

        ctk.CTkLabel(cfg_frame, text="Repository & Output Settings", font=("SF Pro Display", 14, "bold"), text_color=self.accent_cyan).pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(cfg_frame, text="Git Repository Directory:", font=("SF Pro Text", 11), text_color=self.text_secondary).pack(anchor="w", pady=(5, 2))
        repo_row = ctk.CTkFrame(cfg_frame, fg_color="transparent")
        repo_row.pack(fill="x", pady=(0, 10))

        self.repo_entry = ctk.CTkEntry(repo_row, fg_color=self.bg_sidebar, border_color=self.card_border, font=("SF Pro Text", 11), height=35)
        self.repo_entry.insert(0, os.getcwd())
        self.repo_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        browse_btn = ctk.CTkButton(repo_row, text="Browse", image=self.img_folder, compound="left", width=85, height=35, fg_color="#334155", hover_color="#475569", command=self.browse_repo)
        browse_btn.pack(side="right")

        ctk.CTkLabel(cfg_frame, text="Target Timezone:", font=("SF Pro Text", 11), text_color=self.text_secondary).pack(anchor="w", pady=(5, 2))
        self.tz_combo = ctk.CTkComboBox(cfg_frame, values=COMMON_TIMEZONES, fg_color=self.bg_sidebar, border_color=self.card_border, height=35, font=("SF Pro Text", 11))
        self.tz_combo.set("Asia/Kolkata (IST)")
        self.tz_combo.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(cfg_frame, text="Target Activity File:", font=("SF Pro Text", 11), text_color=self.text_secondary).pack(anchor="w", pady=(5, 2))
        self.target_file_entry = ctk.CTkEntry(cfg_frame, fg_color=self.bg_sidebar, border_color=self.card_border, font=("SF Pro Text", 11), height=35)
        self.target_file_entry.insert(0, "activity_log.txt")
        self.target_file_entry.pack(fill="x", pady=(0, 10))

        sch_frame = ctk.CTkFrame(self.tab_dash, fg_color="transparent")
        sch_frame.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)

        ctk.CTkLabel(sch_frame, text="Trigger Frequency & Message", font=("SF Pro Display", 14, "bold"), text_color=self.accent_indigo).pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(sch_frame, text="Commit Message:", font=("SF Pro Text", 11), text_color=self.text_secondary).pack(anchor="w", pady=(5, 2))
        self.msg_entry = ctk.CTkEntry(sch_frame, fg_color=self.bg_sidebar, border_color=self.card_border, font=("SF Pro Text", 11), height=35)
        self.msg_entry.insert(0, "chore: automated activity update")
        self.msg_entry.pack(fill="x", pady=(0, 8))

        preset_row = ctk.CTkFrame(sch_frame, fg_color="transparent")
        preset_row.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(preset_row, text="Presets:", font=("SF Pro Text", 10), text_color=self.text_secondary).pack(side="left", padx=(0, 6))

        for p in PRESET_MESSAGES[:3]:
            btn = ctk.CTkButton(
                preset_row,
                text=p.split(":")[0],
                width=55,
                height=24,
                font=("SF Pro Text", 10),
                fg_color=self.bg_sidebar,
                hover_color=self.card_border,
                command=lambda val=p: self.set_preset(val),
            )
            btn.pack(side="left", padx=2)

        ctk.CTkLabel(sch_frame, text="Schedule Interval:", font=("SF Pro Text", 11), text_color=self.text_secondary).pack(anchor="w", pady=(5, 2))
        freq_row = ctk.CTkFrame(sch_frame, fg_color="transparent")
        freq_row.pack(fill="x", pady=(0, 15))

        self.interval_entry = ctk.CTkEntry(freq_row, width=80, fg_color=self.bg_sidebar, border_color=self.card_border, font=("SF Pro Text", 11), height=35)
        self.interval_entry.insert(0, "1")
        self.interval_entry.pack(side="left", padx=(0, 10))

        self.unit_combo = ctk.CTkComboBox(freq_row, values=["Seconds", "Minutes", "Hours"], width=120, fg_color=self.bg_sidebar, border_color=self.card_border, height=35)
        self.unit_combo.set("Minutes")
        self.unit_combo.pack(side="left")

        act_box = ctk.CTkFrame(sch_frame, fg_color="transparent")
        act_box.pack(fill="x", pady=(10, 0))

        self.start_btn = ctk.CTkButton(
            act_box,
            text=" START AUTOMATION",
            image=self.img_play,
            compound="left",
            font=("SF Pro Text", 12, "bold"),
            fg_color=self.accent_emerald,
            hover_color="#059669",
            height=42,
            corner_radius=8,
            command=self.start_scheduler,
        )
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.stop_btn = ctk.CTkButton(
            act_box,
            text=" STOP",
            image=self.img_stop,
            compound="left",
            width=95,
            font=("SF Pro Text", 12, "bold"),
            fg_color=self.accent_rose,
            hover_color="#e11d48",
            height=42,
            corner_radius=8,
            state="disabled",
            command=self.stop_scheduler,
        )
        self.stop_btn.pack(side="right")

    def set_preset(self, text):
        self.msg_entry.delete(0, "end")
        self.msg_entry.insert(0, text)

    def build_heatmap_tab(self):
        container = ctk.CTkFrame(self.tab_heatmap, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=15)

        # Header Row with Refresh Button
        top_hdr = ctk.CTkFrame(container, fg_color="transparent")
        top_hdr.pack(fill="x", pady=(0, 10))

        titles_box = ctk.CTkFrame(top_hdr, fg_color="transparent")
        titles_box.pack(side="left")

        ctk.CTkLabel(titles_box, text="GitHub Contribution Heatmap", font=("SF Pro Display", 15, "bold"), text_color=self.accent_emerald).pack(anchor="w")
        ctk.CTkLabel(titles_box, text="Real-time Git commit activity mapped directly from repository history.", font=("SF Pro Text", 11), text_color=self.text_secondary).pack(anchor="w")

        sync_btn = ctk.CTkButton(
            top_hdr,
            text="🔄 Sync Git Log",
            font=("SF Pro Text", 11, "bold"),
            width=110,
            height=32,
            fg_color=self.accent_indigo,
            hover_color="#4f46e5",
            command=self.fetch_and_render_git_heatmap,
        )
        sync_btn.pack(side="right")

        # Main Heatmap Card
        grid_card = ctk.CTkFrame(container, fg_color=self.bg_sidebar, corner_radius=12)
        grid_card.pack(fill="both", expand=True, padx=0, pady=(5, 10))

        # Days of week labels (Sun - Sat) on left column
        day_labels_frame = ctk.CTkFrame(grid_card, fg_color="transparent")
        day_labels_frame.pack(side="left", padx=(15, 8), pady=15, fill="y")

        days_short = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        for d in days_short:
            lbl = ctk.CTkLabel(day_labels_frame, text=d, font=("SF Pro Text", 9, "bold"), text_color=self.text_secondary, height=22)
            lbl.pack(pady=2)

        # Grid of 7 rows x 24 columns for 24 weeks (~5.5 months of git commits)
        self.heatmap_grid_frame = ctk.CTkFrame(grid_card, fg_color="transparent")
        self.heatmap_grid_frame.pack(side="left", padx=5, pady=15, fill="both", expand=True)

        self.heatmap_tiles = []
        self.tile_dates = {}  # Map (row, col) to YYYY-MM-DD

        for row in range(7):
            row_tiles = []
            for col in range(24):
                tile = ctk.CTkFrame(self.heatmap_grid_frame, width=22, height=22, fg_color="#161b22", corner_radius=4)
                tile.grid(row=row, column=col, padx=3, pady=2)
                row_tiles.append(tile)
            self.heatmap_tiles.append(row_tiles)

        # Hover Info Bar at bottom
        self.heatmap_info_lbl = ctk.CTkLabel(container, text="Hover over any square to view date & commit count", font=("SF Pro Text", 11), text_color=self.accent_cyan)
        self.heatmap_info_lbl.pack(anchor="w", pady=(2, 0))

        # Legend at bottom right
        legend_frame = ctk.CTkFrame(grid_card, fg_color="transparent")
        legend_frame.pack(side="right", padx=15, pady=15, anchor="se")

        ctk.CTkLabel(legend_frame, text="Less", font=("SF Pro Text", 10), text_color=self.text_secondary).pack(side="left", padx=4)
        colors = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
        for c in colors:
            ctk.CTkFrame(legend_frame, width=14, height=14, fg_color=c, corner_radius=3).pack(side="left", padx=2)
        ctk.CTkLabel(legend_frame, text="More", font=("SF Pro Text", 10), text_color=self.text_secondary).pack(side="left", padx=4)

    def fetch_and_render_git_heatmap(self):
        """Queries target Git repository history and updates heatmap grid with real commit counts."""
        repo_path = self.repo_entry.get().strip()
        if not os.path.exists(repo_path):
            self.log("WARN", f"Repository path not found for heatmap sync: {repo_path}")
            return

        def _worker():
            try:
                repo = Repo(repo_path)
                commit_counts = Counter()
                total_commits_count = 0

                # Iterate commits up to 2000
                for commit in repo.iter_commits(max_count=2000):
                    c_date = datetime.fromtimestamp(commit.committed_date).strftime("%Y-%m-%d")
                    commit_counts[c_date] += 1
                    total_commits_count += 1

                self.total_commits = total_commits_count

                # Calculate date matrix for 7 rows x 24 columns
                today = datetime.now().date()
                # Start date calculation: 23 weeks back + offset to start on Sunday
                start_offset_days = 7 * 23 + (today.weekday() + 1) % 7
                start_date = today - timedelta(days=start_offset_days)

                colors = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]

                # Calculate active streak (consecutive days leading up to today)
                streak = 0
                check_day = today
                while True:
                    day_str = check_day.strftime("%Y-%m-%d")
                    if commit_counts.get(day_str, 0) > 0:
                        streak += 1
                        check_day -= timedelta(days=1)
                    else:
                        # Allow today to be 0 if yesterday was active
                        if check_day == today:
                            check_day -= timedelta(days=1)
                            continue
                        break
                self.streak_days = streak

                # Update UI elements on main thread
                def _update_ui():
                    self.card1_val.configure(text=str(self.total_commits))
                    self.card2_val.configure(text=f"🔥 {self.streak_days} Day{'s' if self.streak_days != 1 else ''}")

                    for col in range(24):
                        for row in range(7):
                            cell_date = start_date + timedelta(days=col * 7 + row)
                            date_str = cell_date.strftime("%Y-%m-%d")
                            count = commit_counts.get(date_str, 0)

                            # Determine intensity color
                            if count == 0:
                                color = colors[0]
                            elif count == 1:
                                color = colors[1]
                            elif 2 <= count <= 4:
                                color = colors[2]
                            elif 5 <= count <= 9:
                                color = colors[3]
                            else:
                                color = colors[4]

                            tile = self.heatmap_tiles[row][col]
                            tile.configure(fg_color=color)

                            # Bind hover tooltip event
                            msg = f"📅 {date_str}  —  {count} commit{'s' if count != 1 else ''}"
                            tile.bind("<Enter>", lambda e, m=msg: self.heatmap_info_lbl.configure(text=m))
                            tile.bind("<Leave>", lambda e: self.heatmap_info_lbl.configure(text="Hover over any square to view date & commit count"))

                self.after(0, _update_ui)
                self.log("INFO", f"Git Heatmap synchronized with {total_commits_count} commits across repository.")

            except Exception as e:
                self.log("ERROR", f"Heatmap sync error: {e}")

        threading.Thread(target=_worker, daemon=True).start()

    def build_logs_tab(self):
        log_card = ctk.CTkFrame(self.tab_logs, fg_color="transparent")
        log_card.pack(fill="both", expand=True, padx=15, pady=15)

        top_row = ctk.CTkFrame(log_card, fg_color="transparent")
        top_row.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(top_row, text="Execution Terminal & Activity Log", font=("SF Pro Display", 14, "bold"), text_color=self.accent_indigo).pack(side="left")

        clear_btn = ctk.CTkButton(top_row, text="Clear Console", width=90, height=28, font=("SF Pro Text", 11), fg_color="#334155", hover_color="#475569", command=self.clear_logs)
        clear_btn.pack(side="right")

        self.log_textbox = ctk.CTkTextbox(log_card, fg_color=self.bg_sidebar, text_color=self.text_primary, font=("Menlo", 11), corner_radius=10, wrap="word")
        self.log_textbox.pack(fill="both", expand=True)

    def switch_tab(self, tab_key):
        if tab_key == "dash":
            self.tabview.set("Automation Dashboard")
            self.nav_btn_dash.configure(fg_color=self.accent_indigo, text_color="#ffffff")
            self.nav_btn_heatmap.configure(fg_color="transparent", text_color=self.text_secondary)
            self.nav_btn_logs.configure(fg_color="transparent", text_color=self.text_secondary)
        elif tab_key == "heatmap":
            self.tabview.set("Contribution Heatmap")
            self.nav_btn_dash.configure(fg_color="transparent", text_color=self.text_secondary)
            self.nav_btn_heatmap.configure(fg_color=self.accent_indigo, text_color="#ffffff")
            self.nav_btn_logs.configure(fg_color="transparent", text_color=self.text_secondary)
            self.fetch_and_render_git_heatmap()
        elif tab_key == "logs":
            self.tabview.set("Execution Console")
            self.nav_btn_dash.configure(fg_color="transparent", text_color=self.text_secondary)
            self.nav_btn_heatmap.configure(fg_color="transparent", text_color=self.text_secondary)
            self.nav_btn_logs.configure(fg_color=self.accent_indigo, text_color="#ffffff")

    def update_live_clock(self):
        tz_name = clean_tz_name(self.tz_combo.get())
        formatted, _ = get_formatted_time(tz_name)
        time_part = formatted.split(" ")[1]
        tz_abbr = formatted.split(" ")[2]
        self.clock_lbl.configure(text=f"{time_part} {tz_abbr}")
        self.after(1000, self.update_live_clock)

    def log(self, tag, message):
        tz_name = clean_tz_name(self.tz_combo.get())
        timestamp_str, _ = get_formatted_time(tz_name)
        formatted = f"[{timestamp_str}] [{tag}] {message}\n"
        self.log_queue.put((tag, formatted))

    def process_log_queue(self):
        while not self.log_queue.empty():
            tag, msg = self.log_queue.get()
            self.log_textbox.insert("end", msg)
            self.log_textbox.see("end")
        self.after(100, self.process_log_queue)

    def clear_logs(self):
        self.log_textbox.delete("1.0", "end")

    def browse_repo(self):
        selected_dir = ctk.filedialog.askdirectory(initialdir=self.repo_entry.get())
        if selected_dir:
            self.repo_entry.delete(0, "end")
            self.repo_entry.insert(0, selected_dir)
            self.fetch_and_render_git_heatmap()

    def update_next_run_time(self):
        if not self.is_running:
            self.card4_val.configure(text="N/A")
            return

        tz_name = clean_tz_name(self.tz_combo.get())
        _, now_tz = get_formatted_time(tz_name)

        if self.unit_val == "Seconds":
            next_t = now_tz + timedelta(seconds=self.interval_val)
        elif self.unit_val == "Hours":
            next_t = now_tz + timedelta(hours=self.interval_val)
        else:
            next_t = now_tz + timedelta(minutes=self.interval_val)

        self.next_commit_str = next_t.strftime("%H:%M:%S")
        self.card4_val.configure(text=self.next_commit_str)

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
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(f"Updated at: {timestamp_str}\n")

            repo = Repo(repo_path)
            repo.git.add(target_file)

            full_msg = f"{commit_msg} [{timestamp_str}]"
            repo.index.commit(full_msg)

            origin = repo.remote(name="origin")
            origin.push()

            self.last_commit_str = now_tz.strftime("%H:%M:%S")
            self.after(0, lambda: self.card3_val.configure(text=self.last_commit_str))

            # Synchronize Real Git Heatmap & Total Commits
            self.after(0, self.fetch_and_render_git_heatmap)

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
            ctk.CTkMessagebox.show_error("Invalid Input", "Interval must be a positive number.")
            return

        self.unit_val = self.unit_combo.get()
        self.is_running = True
        self.stop_event.clear()

        self.sidebar_status_badge.configure(text="● SYSTEM ACTIVE", text_color=self.accent_emerald, fg_color="#122a22")
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.repo_entry.configure(state="disabled")
        self.interval_entry.configure(state="disabled")
        self.tz_combo.configure(state="disabled")

        tz_name = clean_tz_name(self.tz_combo.get())
        self.log("INFO", f"Auto-committer active. Schedule: every {self.interval_val} {self.unit_val} [{tz_name}].")

        self.log("INFO", "Executing initial startup commit...")
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

        self.sidebar_status_badge.configure(text="● SYSTEM STOPPED", text_color=self.accent_rose, fg_color="#2b1725")
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.repo_entry.configure(state="normal")
        self.interval_entry.configure(state="normal")
        self.tz_combo.configure(state="readonly")

        self.card4_val.configure(text="N/A")
        self.log("WARN", "Auto-committer schedule stopped by user.")


def main():
    app = ModernAutoCommitterApp()
    app.mainloop()


if __name__ == "__main__":
    main()
