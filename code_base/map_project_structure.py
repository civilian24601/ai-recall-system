import os
import json
from datetime import datetime

PROJECT_ROOT = "/mnt/f/projects/ai-recall-system"
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "logs/project_structure.json")


def map_directory(root_dir):
    """Recursively maps the entire project directory."""
    project_map = {}
    for root, dirs, files in os.walk(root_dir):
        relative_path = os.path.relpath(root, PROJECT_ROOT)
        project_map[relative_path] = {"dirs": dirs, "files": files}
    return project_map


def save_structure():
    """Saves the mapped project directory to a JSON file."""
    project_structure = {
        "timestamp": datetime.now().isoformat(),
        "structure": map_directory(PROJECT_ROOT),
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(project_structure, f, indent=4)
    print(f"✅ Project directory structure saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    save_structure()
