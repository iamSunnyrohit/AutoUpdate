import json
import os
import random
from datetime import datetime, timezone

# Sample positive activity messages/quotes
QUOTES = [
    "Keep coding and stay consistent!",
    "Small daily improvements lead to massive long-term results.",
    "Consistency is the key to mastery.",
    "Automating the routine, elevating the creation.",
    "Building software one commit at a time.",
    "Code, commit, repeat.",
    "Every commit is a step forward.",
]

LOG_FILE = "activity_log.txt"
DATA_FILE = "data.json"


def update_log():
    now_utc = datetime.now(timezone.utc)
    timestamp_str = now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")

    # Load existing data from JSON if present
    data = {"total_updates": 0, "history": []}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            pass

    data["total_updates"] += 1
    selected_quote = random.choice(QUOTES)

    history_entry = {
        "update_number": data["total_updates"],
        "timestamp": timestamp_str,
        "note": selected_quote,
    }

    # Maintain recent history (last 50 entries) in JSON
    data["history"].append(history_entry)
    if len(data["history"]) > 50:
        data["history"] = data["history"][-50:]

    data["last_updated"] = timestamp_str

    # Save JSON data file
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    # Append to activity_log.txt
    log_line = f"[{timestamp_str}] Update #{data['total_updates']}: {selected_quote}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_line)

    print(f"Successfully recorded update #{data['total_updates']} at {timestamp_str}")


if __name__ == "__main__":
    update_log()
