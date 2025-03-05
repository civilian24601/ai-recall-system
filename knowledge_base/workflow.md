# Workflow: AI Recall System Development

### 🌟 **Overview**

Builds the AI Recall System iteratively via GitHub (dev branch). Keeps chat context lean—repo holds truth. Every success commits, tracked via Issues.

### 🌱 **Setup**

1. Repo: Set <https://github.com/civilian24601/ai-recall-system> to public (unlisted).
2. Branch: Use dev—URL: <https://github.com/civilian24601/ai-recall-system/tree/dev>.
3. Validate Access:
    - Chat picks a file (e.g., scripts/initialize_chroma.py).
    - Prints it verbatim—Alex confirms it matches local copy.

### **🚀 Development Cycle**

1. WORK:
    - **Sync with Repo Truth**:
        1. Pull <https://github.com/civilian24601/ai-recall-system/tree/dev>.
        2. Diff the target file (e.g., `scripts/index_codebase.py`) against the last revision in chat.
        3. Update from the repo’s truth, then apply changes.
    - Pick a piece: script (e.g., `index_codebase.py`), log setup, test, markdown.
    - Chat pulls latest from dev, suggests changes (e.g., “Add hash check here”).
    - Alex edits locally (e.g., in WSL: `nano scripts/index_codebase.py`).
2. VALIDATE:
    - Run it—e.g., python scripts/index_codebase.py or verify_rag.py.
    - Check outputs (e.g., “Indexed 50 files, no dupes”).
    - Fix bugs—chat debugs (e.g., “Try if not os.path.exists()”).
    - Alex confirms: “Works—50 files indexed.”
3. COMMIT:
    - Alex stages: git add scripts/index_codebase.py.
    - Chat writes message with tag: [SCRIPT], [DOC], [TEST], [FIX] (e.g., [SCRIPT] index_codebase.py: added hash dedup, tested 50 files).
    - Alex commits: git commit -m "[SCRIPT] index_codebase.py: added hash dedup, tested 50 files".
    - Push: git push origin dev.
4. REPEAT:
    - Chat picks next piece (e.g., “Now index_knowledgebase.py?”).
    - Alex agrees or pivots (e.g., “Yes” or “Agent first”).

### **🔍 Post-Commit QA**

1. Doc Scan:
    - Chat scans knowledge_base/ (e.g., ls knowledge_base/*.md).
    - Flags updates—e.g., “best_practices.md: add dedup rule.”
    - Alex edits, commits (e.g., [DOC] best_practices.md: added dedup guideline).
2. Repo Re-Scan:
    - Chat pulls dev (e.g., mimics git pull origin dev).
    - Checks impacts—e.g., “index_codebase.py change needs aggregator_search.py tweak.”
    - Alex addresses or notes for later (e.g., “Next cycle”).
3. Issue Check:
    - See “Incorporating GitHub Issues”—log new tasks if found.

### **🛠️ Incorporating GitHub Issues**

Tracks big tasks, gaps, bugs—nothing slips.

🌿 **Process**

1. Identify a Need:
    - During WORK/VALIDATE/QA, spot it (e.g., “Agent RAG timeouts in agent.py”).
    - Chat: “Suggest Issue #[number]: [title]” (e.g., “#1: Agent RAG Timeouts”).
2. Create the Issue (Alex):
    - Go: <https://github.com/civilian24601/ai-recall-system/issues>.
    - Click “New issue”.
    - Title: E.g., “Agent RAG Timeouts in agent.py”.
    - Body:

        *Description -* E.g., “[agent.py](http://agent.py/) stalls on LLM queries—needs RAG fix.”

        *Tasks*

        - [ ]  Debug timeout in query_chroma().
        - [ ]  Test with dummy RAG data.

        *Priority - E.g., “High—blocks self-iteration.”*

        - Submit—gets #1.
        - Share link (e.g., <https://github.com/civilian24601/ai-recall-system/issues/1>).
3. Chat Logs It:
    - Chat: “Issue #1 logged: [URL].”
    - Ties to work (e.g., “Will hit this next”).
4. Work the Issue:
    - WORK cycle references #1.
    - Update Issue—tick tasks (edit Body, [x]), add notes (e.g., “Fixed timeout”).
5. Close It:
    - COMMIT with “Fixes #1” (e.g., [FIX] agent.py: resolved RAG timeout, Fixes #1).
    - Push—GitHub closes #1.
    - Chat: “Issue #1 closed—agent.py fixed.”

🌿 Rules

- Chat suggests issues to open
- Alex opens Issues—chat can’t.
- Chat  tracks, links in commits.
- Small fixes in chat—big gaps get Issues.

📈 Progress Tracking

1. Milestone Check:
    - After 3-5 commits, chat summarizes (e.g., “Indexing done, 2 Issues open”).
    - Alex nods or adjusts (e.g., “Focus agent next”).
2. Issues:
    - Open = todo; closed = done—check <https://github.com/civilian24601/ai-recall-system/issues>.

🧠 Context Management

- Chat pulls dev post-commit—no bloat, repo’s king.

📅 Last Updated: March 04, 2025
