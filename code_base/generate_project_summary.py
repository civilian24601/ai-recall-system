import os
import json

# Define project root and output file
PROJECT_ROOT = "/mnt/f/projects/ai-recall-system/"
OUTPUT_FILE = "/mnt/f/projects/ai-recall-system/logs/project_summary.md"

# File types to include
INCLUDE_EXTENSIONS = {".py", ".md", ".json", ".yml", ".toml"}

def get_file_summary(file_path):
    """Extracts content from the file and summarizes it."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if file_path.endswith(".py"):
                content = "".join(lines[:30])  # Grab first 30 lines for context
            else:
                content = "".join(lines[:50])  # Longer context for docs
        return content.strip()
    except Exception as e:
        return f"Error reading file: {e}"

def generate_project_summary():
    """Generates a markdown summary of the entire project structure with key content."""
    summary = ["# AI Recall System - Project Summary\n"]
    
    # Walk through project directory
    for root, _, files in os.walk(PROJECT_ROOT):
        for file in files:
            file_ext = os.path.splitext(file)[1]
            if file_ext in INCLUDE_EXTENSIONS:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, PROJECT_ROOT)
                
                # Format output
                summary.append(f"## {relative_path}")
                summary.append(f"**File:** `{file}`")
                summary.append(f"**Path:** `{relative_path}`\n")
                summary.append("### Summary:\n")
                summary.append("```" + file_ext[1:] + "\n" + get_file_summary(file_path) + "\n```")
                summary.append("\n---\n")

    # Save summary to markdown
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(summary))

    print(f"✅ Project summary saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_project_summary()
