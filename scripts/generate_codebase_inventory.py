import os

# Define paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CODEBASE_DIRS = [os.path.join(BASE_DIR, "code_base"), os.path.join(BASE_DIR, "scripts")]
OUTPUT_FILE = os.path.join(BASE_DIR, "codebase_inventory.md")
TREE_OUTPUT = os.path.join(BASE_DIR, "codebase_structure.txt")

def generate_directory_tree(output_file, depth=3):
    """Generate a tree structure of the codebase."""
    os.system(f"tree -L {depth} --dirsfirst --filelimit 50 {BASE_DIR} > {output_file}")

def merge_python_files(output_file):
    """Merge all Python scripts from `code_base/` and `scripts/` into a single markdown file."""
    with open(output_file, "w", encoding="utf-8") as outfile:
        for directory in CODEBASE_DIRS:
            for root, _, files in os.walk(directory):
                for file in sorted(files):
                    if file.endswith(".py"):
                        file_path = os.path.join(root, file)
                        outfile.write(f"\n# 📂 {file_path.replace(BASE_DIR + '/', '')}\n\n")
                        with open(file_path, "r", encoding="utf-8") as infile:
                            outfile.write(infile.read())
                        outfile.write("\n---\n")  # Separator between files
    print(f"✅ Codebase inventory saved to {output_file}")

if __name__ == "__main__":
    print("🔄 Generating directory tree...")
    generate_directory_tree(TREE_OUTPUT)
    
    print("🔄 Merging Python scripts into a single file...")
    merge_python_files(OUTPUT_FILE)

    print(f"✅ Directory tree saved to {TREE_OUTPUT}")
    print(f"✅ Codebase inventory saved to {OUTPUT_FILE}")
