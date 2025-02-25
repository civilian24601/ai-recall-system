import os
import datetime
import re

# Base Directories
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
KNOWLEDGE_BASE_DIR = os.path.join(BASE_DIR, "knowledge_base")
CODEBASE_DIRS = [os.path.join(BASE_DIR, "code_base"), os.path.join(BASE_DIR, "scripts")]

# Output Files
COMPILED_KNOWLEDGE_FILE = os.path.join(BASE_DIR, "compiled_knowledge.txt")
CODEBASE_INVENTORY_FILE = os.path.join(BASE_DIR, "codebase_inventory.txt")
TREE_OUTPUT_FILE = os.path.join(BASE_DIR, "codebase_structure.txt")


def slugify(text):
    """Converts a string to a simplified, file-safe version."""
    text = text.lower().replace(" ", "_")
    return re.sub(r"[^a-z0-9_]", "", text)


def convert_markdown_to_text(md_content):
    """Strips Markdown syntax to produce plain text output."""
    md_content = re.sub(r"#+\s*", "", md_content)  # Remove Markdown headers
    md_content = re.sub(r"\*\*(.*?)\*\*", r"\1", md_content)  # Bold -> Plain
    md_content = re.sub(r"\*(.*?)\*", r"\1", md_content)  # Italic -> Plain
    md_content = re.sub(r"`(.*?)`", r"\1", md_content)  # Inline code
    md_content = re.sub(r"!\[.*?\]\(.*?\)", "", md_content)  # Remove images
    md_content = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", md_content)  # Remove links, keep text
    md_content = re.sub(r"-\s", "", md_content)  # Remove bullet points
    return md_content.strip()


def generate_table_of_contents(text_files):
    """Creates a table of contents for the knowledge base."""
    toc_lines = ["Table of Contents", ""]
    for filename in text_files:
        title = os.path.splitext(filename)[0]
        toc_lines.append(f"- {title}")
    toc_lines.append("")
    return "\n".join(toc_lines)


def merge_markdown_files(source_folder, output_file):
    """Merges all .md files into a single .txt file, stripping Markdown syntax."""
    if not os.path.exists(source_folder):
        print(f"❌ ERROR: Source folder '{source_folder}' does not exist.")
        return

    md_files = sorted([f for f in os.listdir(source_folder) if f.endswith(".md")])

    if not md_files:
        print("⚠️ No markdown files found to compile.")
        return

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = f"Compiled Knowledge Base\nLast updated: {timestamp}\n\n"

    toc = generate_table_of_contents(md_files)

    with open(output_file, "w", encoding="utf-8") as outfile:
        outfile.write(header)
        outfile.write(toc)
        outfile.write("\n" + "=" * 50 + "\n\n")

        for filename in md_files:
            file_path = os.path.join(source_folder, filename)
            with open(file_path, "r", encoding="utf-8") as infile:
                raw_content = infile.read()
                plain_text = convert_markdown_to_text(raw_content)
                title = os.path.splitext(filename)[0]
                outfile.write(f"\n{title.upper()}\n")
                outfile.write("-" * len(title) + "\n\n")
                outfile.write(plain_text)
                outfile.write("\n" + "-" * 50 + "\n")

    print(f"✅ Merged markdown files saved to: {output_file}")


def generate_directory_tree(output_file, depth=3):
    """Generates a tree structure of the codebase."""
    os.system(f"tree -L {depth} --dirsfirst --filelimit 50 {BASE_DIR} > {output_file}")


def merge_python_files(output_file):
    """Merges all Python scripts from `code_base/` and `scripts/` into a single text file."""
    with open(output_file, "w", encoding="utf-8") as outfile:
        for directory in CODEBASE_DIRS:
            for root, _, files in os.walk(directory):
                for file in sorted(files):
                    if file.endswith(".py"):
                        file_path = os.path.join(root, file)
                        outfile.write(f"\nFILE: {file_path.replace(BASE_DIR + '/', '')}\n")
                        outfile.write("=" * 50 + "\n")
                        with open(file_path, "r", encoding="utf-8") as infile:
                            outfile.write(infile.read())
                        outfile.write("\n" + "-" * 50 + "\n")

    print(f"✅ Codebase inventory saved to {output_file}")


if __name__ == "__main__":
    print("🔄 Generating directory tree...")
    generate_directory_tree(TREE_OUTPUT_FILE)

    print("🔄 Merging knowledge base files into a single text file (Markdown -> Plain Text)...")
    merge_markdown_files(KNOWLEDGE_BASE_DIR, COMPILED_KNOWLEDGE_FILE)

    print("🔄 Merging Python scripts into a single text file...")
    merge_python_files(CODEBASE_INVENTORY_FILE)

    print(f"✅ Directory tree saved to {TREE_OUTPUT_FILE}")
    print(f"✅ Compiled knowledge saved to {COMPILED_KNOWLEDGE_FILE}")
    print(f"✅ Codebase inventory saved to {CODEBASE_INVENTORY_FILE}")
