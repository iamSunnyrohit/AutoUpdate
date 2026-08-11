import os
import sys
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from git import Repo, GitCommandError
import schedule


def get_formatted_time(tz_name="Asia/Kolkata"):
    try:
        tz = ZoneInfo(tz_name)
        now = datetime.now(tz)
        return now.strftime("%Y-%m-%d %H:%M:%S %Z (UTC%z)")
    except Exception:
        now = datetime.now(timezone.utc)
        return now.strftime("%Y-%m-%d %H:%M:%S UTC")


def make_commit(repo_path, commit_message, target_file="activity_log.txt", tz_name="Asia/Kolkata"):
    """Appends timestamp to file and commits changes to Git."""
    file_path = os.path.join(repo_path, target_file)
    timestamp = get_formatted_time(tz_name)

    try:
        # 1. Update target file
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"Updated at: {timestamp}\n")

        repo = Repo(repo_path)

        # 2. Stage changes
        repo.git.add(target_file)

        # 3. Commit
        full_message = f"{commit_message} [{timestamp}]"
        repo.index.commit(full_message)

        # 4. Push
        origin = repo.remote(name="origin")
        origin.push()

        print(f"[{timestamp}] Successfully committed & pushed: '{full_message}'")
        return True

    except GitCommandError as e:
        print(f"[{timestamp}] Git error occurred: {e}")
        return False
    except Exception as e:
        print(f"[{timestamp}] Error: {e}")
        return False


def main():
    print("========================================")
    print("     Interactive Auto-Committer CLI    ")
    print("========================================\n")

    repo_path = os.getcwd()
    print(f"[i] Working directory: {repo_path}")

    # Prompt user for timezone selection
    print("\nSelect Timezone:")
    print("1. Indian Standard Time - IST (Asia/Kolkata) [Default]")
    print("2. UTC (Coordinated Universal Time)")
    print("3. Custom Timezone String (e.g., America/New_York, Europe/London)")
    tz_choice = input("Enter choice (1/2/3, default 1): ").strip()

    tz_name = "Asia/Kolkata"
    if tz_choice == "2":
        tz_name = "UTC"
    elif tz_choice == "3":
        custom_tz = input("Enter timezone name (e.g., America/New_York): ").strip()
        try:
            ZoneInfo(custom_tz)
            tz_name = custom_tz
        except ZoneInfoNotFoundError:
            print(f"Unknown timezone '{custom_tz}'. Defaulting to Asia/Kolkata (IST).")
            tz_name = "Asia/Kolkata"

    print(f"[+] Active Timezone: {tz_name} (Current time: {get_formatted_time(tz_name)})")

    # Prompt user for commit message
    commit_msg = input("\nEnter custom commit message (default: 'chore: automated update'): ").strip()
    if not commit_msg:
        commit_msg = "chore: automated update"

    # Prompt user for interval duration
    print("\nSelect interval unit:")
    print("1. Minutes")
    print("2. Hours")
    print("3. Seconds (for quick testing)")
    choice = input("Enter choice (1/2/3, default 1): ").strip()

    try:
        interval = float(input("Enter interval frequency (e.g., 30 for mins, 1 for hr): ").strip())
    except ValueError:
        print("Invalid input. Defaulting to 60 minutes.")
        interval = 60
        choice = "1"

    # Set up scheduling based on user input
    if choice == "2":
        schedule.every(interval).hours.do(make_commit, repo_path=repo_path, commit_message=commit_msg, tz_name=tz_name)
        unit = "hour(s)"
    elif choice == "3":
        schedule.every(interval).seconds.do(make_commit, repo_path=repo_path, commit_message=commit_msg, tz_name=tz_name)
        unit = "second(s)"
    else:
        schedule.every(interval).minutes.do(make_commit, repo_path=repo_path, commit_message=commit_msg, tz_name=tz_name)
        unit = "minute(s)"

    print(f"\n[+] Auto-committer started! Running every {interval} {unit} [{tz_name}].")
    print("Press Ctrl + C to stop the process anytime.\n")

    # Initial commit
    print("Performing initial commit...")
    make_commit(repo_path, commit_msg, tz_name=tz_name)

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[!] Auto-committer stopped by user. Exiting safely.")
        sys.exit(0)


if __name__ == "__main__":
    main()
