import os

# Define paths
knowledge_base_path = "/mnt/f/projects/ai-recall-system/knowledge_base/"
log_file = "/mnt/f/projects/ai-recall-system/progress_log.md"

# Scan knowledge base
def scan_knowledge_base():
    knowledge_files = [f for f in os.listdir(knowledge_base_path) if f.endswith(".md")]

    summary = f"# AI Knowledge Base Scan\n\nFound {len(knowledge_files)} knowledge files:\n\n"
    for file in knowledge_files:
        summary += f"- {file}\n"
    
    # Write to progress log
    with open(log_file, "w") as f:
        f.write(summary)
    
    print("✅ Knowledge base scan complete. Logged results in `progress_log.md`.")

# Run scan
scan_knowledge_base()
