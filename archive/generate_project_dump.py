import os

# Define project root and output file
PROJECT_ROOT = "/mnt/f/projects/ai-recall-system/"
OUTPUT_FILE = "/mnt/f/projects/ai-recall-system/logs/project_full_dump.md"

# File types to include
INCLUDE_EXTENSIONS = {".py", ".md", ".json", ".yml", ".toml"}

def extract_file_contents(file_path):
    """Reads full content of the file while preserving its formatting."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception as e:
        return f"⚠ Error reading file: {e}"

def generate_project_dump():
    """Generates a full project dump including all relevant files and summaries."""
    dump_content = ["# AI Recall System - Full Project Dump\n"]

    # Walk through project directory
    for root, _, files in os.walk(PROJECT_ROOT):
        for file in files:
            file_ext = os.path.splitext(file)[1]
            if file_ext in INCLUDE_EXTENSIONS:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, PROJECT_ROOT)

                # Extract full content
                file_content = extract_file_contents(file_path)

                # Format output
                dump_content.append(f"## `{relative_path}`")
                dump_content.append(f"**File:** `{file}`")
                dump_content.append(f"**Path:** `{relative_path}`\n")
                dump_content.append(f"### Summary:\n🔹 This file is a **{file_ext[1:].upper()} file**, containing {'Python code' if file_ext == '.py' else 'documentation' if file_ext == '.md' else 'configuration settings'}.\n")
                dump_content.append(f"### Full Content:\n```{file_ext[1:]}\n{file_content}\n```")
                dump_content.append("\n---\n")

    # Save full dump to markdown
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(dump_content))

    print(f"✅ Full project dump saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_project_dump()
