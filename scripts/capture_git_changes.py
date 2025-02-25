import subprocess
import datetime

def get_git_changes():
    """Retrieves all unstaged & staged changes from Git."""
    try:
        diff_output = subprocess.run(["git", "diff"], capture_output=True, text=True).stdout
        staged_output = subprocess.run(["git", "diff", "--staged"], capture_output=True, text=True).stdout
        return diff_output, staged_output
    except Exception as e:
        return f"Error retrieving Git changes: {e}", ""

def log_git_changes():
    """Logs git changes into work session log."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    diff, staged = get_git_changes()

    log_entry = f"## [{timestamp}] Code Changes\n"
    if diff.strip():
        log_entry += f"🔹 **Unstaged Changes:**\n```\n{diff}\n```\n"
    if staged.strip():
        log_entry += f"🔹 **Staged Changes:**\n```\n{staged}\n```\n"

    with open("../logs/work_session.md", "a") as f:
        f.write(log_entry + "\n")

    print("✅ Git changes logged successfully.")

if __name__ == "__main__":
    log_git_changes()
