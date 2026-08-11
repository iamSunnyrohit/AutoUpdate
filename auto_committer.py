import os
import sys
import time
from datetime import datetime
from git import Repo, GitCommandError
import schedule


def make_commit(repo_path, commit_message, target_file="activity_log.txt"):
    """Appends timestamp to file and commits changes to Git."""
    file_path = os.path.join(repo_path, target_file)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        # 1. Update the target file
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"Updated at: {timestamp}\n")

        repo = Repo(repo_path)

        # 2. Stage changes
        repo.git.add(target_file)

        # 3. Commit
        full_message = f"{commit_message} [{timestamp}]"
        repo.index.commit(full_message)

        # 4. Push to remote
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

    # Prompt user for commit message
    commit_msg = input("Enter custom commit message (default: 'chore: automated update'): ").strip()
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
        schedule.every(interval).hours.do(make_commit, repo_path=repo_path, commit_message=commit_msg)
        unit = "hour(s)"
    elif choice == "3":
        schedule.every(interval).seconds.do(make_commit, repo_path=repo_path, commit_message=commit_msg)
        unit = "second(s)"
    else:
        schedule.every(interval).minutes.do(make_commit, repo_path=repo_path, commit_message=commit_msg)
        unit = "minute(s)"

    print(f"\n[+] Auto-committer started! Running every {interval} {unit}.")
    print("Press Ctrl + C to stop the process anytime.\n")

    # Perform an initial commit immediately
    print("Performing initial commit...")
    make_commit(repo_path, commit_msg)

    # Infinite loop running until user terminates script
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[!] Auto-committer stopped by user. Exiting safely.")
        sys.exit(0)


if __name__ == "__main__":
    main()
