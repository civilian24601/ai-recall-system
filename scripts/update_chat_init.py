import os
import subprocess
import json
from datetime import datetime

CHAT_INIT_PATH = "/mnt/f/projects/ai-recall-system/knowledge_base/chat_init.md"
ISSUES_URL = "https://api.github.com/repos/civilian24601/ai-recall-system/issues?state=open"

def get_latest_commit():
    return subprocess.check_output(["git", "log", "-1", "--pretty=format:%H"]).decode().strip()

def get_chunk_counts():
    counts = subprocess.check_output(["python", "scripts/inspect_collections.py"]).decode()
    return {line.split(" => ")[0].split(": ")[1]: int(line.split(" => ")[1].split()[0]) for line in counts.splitlines() if "=>" in line}

def get_open_issues():
    # Placeholder—needs auth token for real API call
    return ["#1-#7"]  # Replace with curl or requests to ISSUES_URL

def update_chat_init():
    commit = get_latest_commit()
    counts = get_chunk_counts()
    issues = get_open_issues()
    date = datetime.now().strftime("%Y-%m-%d")

    content = f"""# 🌟 Chat Initialization - AI Recall System

## 📌 Purpose
Syncs chat sessions with the AI Recall System’s state—current, future, and how to stay fresh. Repo truth drives all: <https://github.com/civilian24601/ai-recall-system/tree/dev>.

## 📊 Current State ({date})
- **Indexing**: 
  - `project_codebase`: {counts.get('project_codebase', 0)} chunks (105 files: /code_base/, /scripts/, /tests/, /frontend/).
  - `knowledge_base`: {counts.get('knowledge_base', 0)} chunks (25 .md files: /knowledge_base/, /agent_knowledge_bases/).
- **Logging**: /logs/script_logs/—e.g., “Processed 105 files, 110 chunks”.
- **Commits**: Latest `{commit}`—logging tweaks, doc updates.
- **Issues**: Open {', '.join(issues)}—e.g., #3 (test/prod split), #4 (README dupes).

## 🚀 Expected Future State
- **Next**: Agents—`agent.py` (engineer), `agent_manager.py` (reviewer)—RAG loop by Q2 2025.
- **Mid-Term**: Multi-project sync—`global_knowledge_base`, tool TBD (~Q2 2025).
- **Endgame**: Self-building apps—city of agents, billion-dollar toolkit.

## 📡 Stay Fresh Formula
- **Daily Update**: Run `scripts/update_chat_init.py`—pulls:
  - `git log -1` (latest commit).
  - `inspect_collections.py` (chunk counts).
  - GitHub Issues API (open Issues: {', '.join(issues)}).
- **Output**: Overwrites this file—commit daily: `[DOC] chat_init.md: daily state update`.

## 🌱 Workflow Tie-In
- Follow `knowledge_base/Workflow.md`—repo truth, Issues track gaps, chats disposable.

Last Updated: {date}
"""
    with open(CHAT_INIT_PATH, "w") as f:
        f.write(content)

if __name__ == "__main__":
    update_chat_init()