import os
import datetime
import re

# Dynamically resolve the absolute path to ai-recall-system
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
KNOWLEDGE_BASE_DIR = os.path.join(BASE_DIR, "knowledge_base")
OUTPUT_FILE = os.path.join(BASE_DIR, "compiled_knowledge.md")

def slugify(text):
    """
    Converts a string to a slug suitable for markdown anchor links.
    """
    text = text.lower()
    text = re.sub(r'\s+', '-', text)
    text = re.sub(r'[^a-z0-9\-]', '', text)
    return text

def generate_table_of_contents(markdown_files):
    """
    Creates a markdown formatted table of contents with links to each file's section.
    """
    toc_lines = ["# Table of Contents", ""]
    for filename in markdown_files:
        title = os.path.splitext(filename)[0]
        anchor = slugify(title)
        toc_lines.append(f"- [{title}](#{anchor})")
    toc_lines.append("")  # add a blank line at the end
    return "\n".join(toc_lines)

def merge_markdown_files(source_folder, output_file):
    """Merges all markdown files in a folder into a single, well-formatted document."""
    if not os.path.exists(source_folder):
        print(f"❌ ERROR: Source folder '{source_folder}' does not exist.")
        return

    # Get a sorted list of markdown files
    md_files = sorted([f for f in os.listdir(source_folder) if f.endswith(".md") and os.path.isfile(os.path.join(source_folder, f))])
    
    # Prepare a timestamp for the document header
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = f"# Compiled Knowledge Base\n\n_Last updated: {timestamp}_\n\n"
    
    # Generate a table of contents
    toc = generate_table_of_contents(md_files)
    
    # Open the output file for writing (this will overwrite previous contents)
    with open(output_file, "w", encoding="utf-8") as outfile:
        # Write the header and TOC
        outfile.write(header)
        outfile.write(toc)
        outfile.write("\n\n---\n\n")
        
        # Process each markdown file
        for filename in md_files:
            file_path = os.path.join(source_folder, filename)
            with open(file_path, "r", encoding="utf-8") as infile:
                title = os.path.splitext(filename)[0]
                anchor = slugify(title)
                # Write a section header with an anchor
                outfile.write(f"\n\n# {title}\n")
                outfile.write(f"<a name=\"{anchor}\"></a>\n\n")
                outfile.write(infile.read())
                outfile.write("\n\n---\n")
    
    print(f"✅ All markdown files merged into: {output_file}")

# Execute with resolved paths
merge_markdown_files(KNOWLEDGE_BASE_DIR, OUTPUT_FILE)
