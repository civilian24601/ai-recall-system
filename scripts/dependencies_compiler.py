import os
import re

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
CODEBASE_DIRS = [os.path.join(BASE_DIR, "code_base"), os.path.join(BASE_DIR, "scripts")]
OUTPUT_FILE = os.path.join(BASE_DIR, "dependencies_report.md")

def extract_imports_from_file(file_path):
    """Extracts import statements from a Python file."""
    imports = set()
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            match = re.match(r"^\s*(?:import|from)\s+([a-zA-Z0-9_\.]+)", line)
            if match:
                imports.add(match.group(1))
    return imports

def generate_dependency_report(output_file):
    """Scans the codebase for dependencies and writes them to a report."""
    dependencies = set()
    for directory in CODEBASE_DIRS:
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    dependencies.update(extract_imports_from_file(file_path))

    # Write results to a markdown file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# 📦 AI Recall System - Dependencies Report\n\n")
        f.write("## 🔹 Identified Python Dependencies\n")
        for dep in sorted(dependencies):
            f.write(f"- `{dep}`\n")

    print(f"✅ Dependencies report saved to {output_file}")

if __name__ == "__main__":
    generate_dependency_report(OUTPUT_FILE)
