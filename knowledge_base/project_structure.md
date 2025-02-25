# AI Recall System – Project Structure Guide

## 📌 Overview
This document outlines the **directory structure** of the AI Recall System. Each folder has a **specific purpose** to facilitate effective knowledge retrieval, debugging recall, multi-agent orchestration, and code management.

Below is the **most up-to-date** tree, with brief descriptions of how the AI interacts or modifies each part of the project.

---

## 📁 Root Directory
**Location:** `/mnt/f/projects/ai-recall-system/`

| **Folder/File**                 | **Purpose**                                                                                          |
|---------------------------------|------------------------------------------------------------------------------------------------------|
| `__pycache__`                   | Python bytecode cache (ignored).                                                                     |
| `agent_knowledge_bases`         | Per-agent knowledge (architect, engineer, QA, etc.).                                                 |
| `archive`                       | Outdated or superseded files, kept for historical reference.                                         |
| `chroma_db`                     | Local Chroma vector database storage (semantic logs, code chunks, etc.).                            |
| `code_base`                     | Main AI code scripts / modules (agents, pipelines, managers).                                        |
| `config`                        | Configuration files for AI settings & environment variables (if any).                               |
| `docs`                          | Additional doc references (pipeline_overview, testing_plan, etc.).                                   |
| `experiments`                   | Sandbox for testing AI scripts & prototypes without affecting the main code.                        |
| `knowledge_base`                | Core knowledge references (merged or single docs).                                                  |
| `logs`                          | Execution logs, debug records, daily summaries, etc.                                                |
| `notion_docs`                   | Imported or generated docs from Notion (work summaries, inventory, etc.).                           |
| `scripts`                       | Standalone scripts for automation, aggregator searches, code indexing, etc.                        |
| `tests`                         | Test scripts for validating AI logic.                                                               |
| `codebase_inventory.md`         | Merged Python script listing from a generation script.                                              |
| `codebase_inventory.txt`        | Text-based listing of the codebase (alternative format).                                            |
| `codebase_inventory_V2.md`      | Possibly a second iteration of the codebase inventory.                                              |
| `codebase_structure.txt`        | Older snapshot of the project directory.                                                            |
| `compiled_knowledge.md`         | Single-file merged knowledge from `.md` docs.                                                       |
| `compiled_knowledge.txt`        | Text version of the compiled knowledge.                                                             |
| `dependencies_report.md`        | Dependencies auto-compiled from Python imports.                                                     |

---

## 📂 `agent_knowledge_bases/`
**Location:** `/mnt/f/projects/ai-recall-system/agent_knowledge_bases/`  
**Purpose:** Stores **agent-specific knowledge** for specialized roles.

| **Subfolder**            | **Purpose**                                                     |
|--------------------------|-----------------------------------------------------------------|
| `architect_knowledge`    | Holds architecture/design references for the Architect agent.   |
| `devops_knowledge`       | Deployment & infrastructure tips (e.g., `deployment_strategy.md`). |
| `engineer_knowledge`     | General code implementation knowledge.                          |
| `feedback_knowledge`     | AI adaptation from user feedback & improvements.               |
| `oversight_knowledge`    | Oversight frameworks for quality control.                      |
| `qa_knowledge`           | Testing methodologies & automated validation.                  |
| `reviewer_knowledge`     | AI-guided code review best practices.                          |

**AI Behavior**:  
- Each specialized agent (Architect, Engineer, QA, etc.) loads knowledge from its subfolder.
- Updated as the system evolves or receives new best practices.

---

## 📂 `archive/`
**Location:** `/mnt/f/projects/ai-recall-system/archive/`  
**Purpose:** Stores **outdated** or **superseded** files for historical context or fallback.

| **File**                     | **Previous Purpose**                                          |
|-----------------------------|---------------------------------------------------------------|
| `ai_debugging_debriefs.md`  | Old debugging log format doc (merged).                        |
| `anticipated_complexities.md`| Originally separate complexities doc (now in future_proofing). |
| `bootstrap_scan.py`         | Early system scan script (likely superseded).                |
| `generate_debug_report.py`  | Used Continue.dev for debug reports.                         |
| `generate_project_dump.py`  | Possibly large project dump creation.                        |
| `project_advanced_details.md`| Merged into advanced design decisions doc.                   |
| `roadmap.md`                | Old roadmap doc, now in `long_term_vision_and_roadmap`.       |
| `start_chromadb.py`         | Simple test script for Chroma (deprecated).                   |
| `txt_compiler.py`           | Possibly compiled text or `.md` files.                        |
| `user_interaction_flow.md`  | Early doc on user flows (absorbed into final docs).           |

**AI Behavior**:  
- **Not used** in active recall unless explicitly asked.  
- Major project pivots move older or replaced files here.

---

## 📂 `chroma_db/`
**Location:** `/mnt/f/projects/ai-recall-system/chroma_db/`  
**Purpose:** **Local** Chroma vector database for semantic retrieval (logs, code references, etc.).

- Subfolders (`xxxx-xxxx-xxxx-...`) contain binary data for Chroma (header, link_lists, etc.).  
- **AI Behavior**: The AI indexes and queries embeddings here for code or debugging solutions.  

*(No need to detail each subfolder—Chroma’s internal structure.)*

---

## 📂 `code_base/`
**Location:** `/mnt/f/projects/ai-recall-system/code_base/`  
**Purpose:** Main **AI code** folder, including agents, debugging logic, pipeline scripts.

| **Folder/File**               | **Description**                                                              |
|-------------------------------|------------------------------------------------------------------------------|
| `__pycache__`                 | Python cache.                                                                |
| `agents/`                     | Specialized agent scripts (Architect, DevOps, Engineer, QA, etc.).           |
| `test_scripts/`               | Extra test modules (e.g. `test_math_operations.py`, `test_db_handler.py`).    |
| `agent_manager.py`            | Orchestrates multi-agent tasks & interactions.                               |
| `api_structure.py`            | Flask endpoints for local model queries & debugging.                         |
| `core_architecture.py`        | Central pipeline logic (loads knowledge, merges with LLM calls).             |
| `debugging_strategy.py`       | AI debugging approach, success metrics, and strategy logs.                   |
| `generate_knowledge_base.py`  | Creates subfolders/README in `agent_knowledge_bases/`.                       |
| `generate_project_summary.py` | Summarizes the entire project with file snippets or partial code.            |
| `generate_work_summary.py`    | Produces daily AI summaries from `work_sessions`.                            |
| `map_project_structure.py`    | Recursively maps directories, storing structure in logs.                     |
| `multi_agent_workflow.py`     | Prototype multi-agent logic.                                                 |
| `network_utils.py`            | Shared environment detection (WSL vs local) & other network logic.           |
| `store_markdown_in_chroma.py` | Automates indexing of `.md` files into Chroma.                               |
| `user_interaction_flow.py`    | CLI-based user queries, fallback to LLM or knowledge base.                    |
| `work_session_logger.py`      | Logs AI work sessions (`files_changed`, `outcome`) into `.md` + Chroma.      |

**AI Behavior**:  
- The **core** area where AI modifies or adds code for new features (debugging, multi-agent tasks).
- Agents and advanced debugging logic revolve around these scripts.

---

## 📂 `config/`
**Location:** `/mnt/f/projects/ai-recall-system/config/`  
**Purpose:**  
- Potential home for **global AI settings** or environment variables.  
- **AI Behavior**: Typically not altered unless told to modify config parameters.

---

## 📂 `docs/`
**Location:** `/mnt/f/projects/ai-recall-system/docs/`

| **File**                 | **Description**                           |
|--------------------------|-------------------------------------------|
| `pipeline_overview.md`   | Possibly an older doc on pipeline steps.  |
| `testing_plan.md`        | High-level or example test plan.          |

**Purpose:** Additional references not in `knowledge_base`.  
**AI Behavior**: The AI might read these if relevant, but less central than `knowledge_base`.

---

## 📂 `experiments/`
**Location:** `/mnt/f/projects/ai-recall-system/experiments/`  
**Purpose:**  
- **Sandbox** for trial AI scripts or agent expansions.  
- **AI Behavior**: May store prototypes here until stable enough for `code_base`.

---

## 📂 `knowledge_base/`
**Location:** `/mnt/f/projects/ai-recall-system/knowledge_base/`

| **File Name**                                         | **Description**                                                           |
|-------------------------------------------------------|---------------------------------------------------------------------------|
| `ai_and_user_interaction_guidelines.md`               | Merged doc about AI ↔ user interaction flow.                              |
| `ai_coding_guidelines.md`                             | Standards for code clarity, docstrings, naming, etc.                      |
| `api_structure.md`                                    | Possibly older doc about the API design approach.                         |
| `best_practices.md`                                   | General best practices for code, debugging, doc generation, etc.          |
| `blueprint_execution_log_template.md`                 | Template for blueprint-based execution logs.                               |
| `core_architecture.md`                                | Summaries of single-agent → multi-agent design (earlier doc).             |
| `debugging_strategy_and_debriefing.md`                | Merged doc: debugging recall strategy & standardized debrief format.      |
| `future_proofing_and_complexities.md`                 | Merged doc on system adaptability & potential challenges.                 |
| `long_term_vision_and_roadmap.md`                     | Merged doc for the phased approach to full AI autonomy.                   |
| `project_overview.md`                                 | High-level summary of the AI Recall System’s scope/goals.                 |
| `project_structure.md`                                | This doc – the latest project structure reference.                         |
| `technical_design_decisions_and_advanced_details.md`  | Merged doc for design decisions & advanced expansions.                    |
| `testing_plan.md`                                     | Possibly an updated doc for testing approaches.                            |

**Purpose:**  
- **Core** references & guidelines the AI checks before generating code.  
- **AI Behavior**: These `.md` docs are typically indexed in Chroma; the AI consults them for best practices or domain knowledge.

---

## 📂 `logs/`
**Location:** `/mnt/f/projects/ai-recall-system/logs/`

| **File/Folder**                  | **Description**                                                     |
|----------------------------------|---------------------------------------------------------------------|
| `LMStudio_DevLogs`               | Logs from the local LM Studio environment.                          |
| `daily_summary.json`             | JSON-based daily AI summaries.                                      |
| `daily_summary.md`               | Markdown daily summary of tasks/outcomes.                           |
| `debug_logs.json`                | Main log of errors & fixes for debugging recall.                    |
| `debug_logs_old.json`            | An older or backup debug log.                                       |
| `debugging_strategy_log.json`    | Tracks success/failure rates of debugging strategies.               |
| `project_full_dump.md`           | Large snapshot of the entire system state.                          |
| `project_structure.json`         | Output from `map_project_structure.py`.                             |
| `work_session.md`                | Tracks manual or AI-coded session logs (files changed, outcome).    |

**Purpose:**  
- **Central** location for storing logs (debug, daily summaries, blueprint execution, etc.).  
- **AI Behavior**: The AI references `debug_logs.json` to recall prior solutions; it may also store daily or session updates here.

---

## 📂 `notion_docs/`
**Location:** `/mnt/f/projects/ai-recall-system/notion_docs/`

| **File**                                           | **Description**                                     |
|----------------------------------------------------|-----------------------------------------------------|
| `2-12 work summary 1982d727cb5...md`               | Possibly a dev/work summary from Notion.            |
| `Hyper-Sprint to MVP 1972d727...md`                | Plan or notes for quickly reaching an MVP.          |
| `Inventory_Report 1972d727...md`                   | Some inventory or resource overview from Notion.    |

**Purpose:**  
- Contains docs imported from or generated for **Notion** references.  
- **AI Behavior**: May parse or store them if relevant, but typically less central.

---

## 📂 `scripts/`
**Location:** `/mnt/f/projects/ai-recall-system/scripts/`

| **File**                             | **Description**                                                                      |
|-------------------------------------|--------------------------------------------------------------------------------------|
| `__pycache__`                       | Python cache for these scripts.                                                     |
| `aggregator_search.py`             | Queries multiple Chroma collections for top N matches.                              |
| `blueprint_execution.py`           | Manages blueprint logs, thresholds, revision proposals.                              |
| `capture_git_changes.py`           | Logs git diffs into `work_session.md`.                                              |
| `check_doc_count.py`               | Quick doc count check in a chosen Chroma collection.                                 |
| `cleanup_collections.py`           | Inspects/deletes old Chroma collections; deletion code often commented out.         |
| `compiled_knowledge.py`            | Merges multiple `.md` docs into one compiled file w/ Table of Contents.             |
| `debug_chroma.py`                  | Dumps raw data from chosen Chroma collections for debugging.                        |
| `dependencies_compiler.py`         | Extracts Python imports from codebase -> `dependencies_report.md`.                  |
| `generate_codebase_inventory.py`    | Produces a `tree` of the codebase & merges `.py` scripts into `codebase_inventory.md`. |
| `index_codebase.py`                | Splits code files into chunks, indexes them in the `project_codebase` collection.    |
| `initialize_chroma.py`             | Creates standard Chroma collections (debugging_logs, blueprint_revisions, etc.).     |
| `log_work_session.py`              | Logs a single “work session” entry into `work_session.md` + Chroma.                 |
| `query_chroma.py`                  | Retrieves data from multiple Chroma collections (knowledge_base, debugging, etc.).   |
| `query_codebase_chunks.py`         | Naive substring search in the `project_codebase` collection.                         |
| `retrieve_codebase.py`             | Embedding-based code snippet retrieval from `project_codebase`.                     |
| `store_test_data.py`               | Overwrites named Chroma collections with known test docs for dev usage.             |

**Purpose:**  
- **Standalone** utilities for indexing code, aggregator searches, data retrieval, etc.  
- **AI Behavior**: The AI can call or modify these scripts as it refines indexing or aggregator logic.

---

## 📂 `tests/`
**Location:** `/mnt/f/projects/ai-recall-system/tests/`

| **File**                       | **Description**                                               |
|--------------------------------|--------------------------------------------------------------|
| `__pycache__`                  | Bytecode cache for test files.                               |
| `test_agent_manager.py`        | Validates the agent manager’s multi-agent workflow logic.     |
| `test_blueprint_execution.py`  | Checks blueprint execution flows & threshold triggers.        |
| `test_query_chroma.py`         | Ensures aggregator or direct Chroma queries function properly.|

**Purpose:**  
- Houses **unit & integration tests** ensuring AI logic (multi-agent, blueprint exec, debugging recall) works correctly.  
- **AI Behavior**: Can update these tests to validate new features or expansions.

---

## Key AI Behaviors

1. **Knowledge Retrieval** – Reads `.md` docs in `knowledge_base/`, indexes them in Chroma, consults them for best practices.  
2. **Debugging & Logging** – Uses `debug_logs.json`, `work_session.md`, blueprint logs to store or retrieve solutions.  
3. **Multi-Agent Collaboration** – Specialized agents in `code_base/agents/` rely on `agent_knowledge_bases/` for domain-specific strategies.  
4. **Script Enhancement** – AI may improve aggregator logic, code indexing, or retrieval scripts in `scripts/`.  
5. **Experimentation** – Prototypes in `experiments/` until stable enough for `code_base/`.

---

## Additional Notes

- **`retrieve_codebase.py`** uses embedding-based retrieval from `project_codebase`, complementing aggregator_search.  
- **`generate_knowledge_base.py`** populates subfolders under `agent_knowledge_bases/`.  
- **`map_project_structure.py`** creates a structure snapshot in `logs/project_structure.json`.  
- **`store_markdown_in_chroma.py`** indexes `.md` from `logs/` & `knowledge_base/` into a separate `markdown_logs` collection.  
- **`cleanup_collections.py`** can list or remove old Chroma collections if they become obsolete.

---

## Summary

This **Project Structure Guide** reflects the **latest** layout of the AI Recall System:

- **agent_knowledge_bases/** – Per-agent knowledge
- **code_base/** – Main AI scripts, multi-agent logic, debugging strategies
- **scripts/** – Standalone utilities (indexing, aggregator, code retrieval)
- **logs/** – Central logging for debugging, daily/blueprint logs, session tracking
- **knowledge_base/** – Core docs & best practices the AI references
- Other supporting folders: **archive**, **experiments**, **tests**, **docs**, etc.

Maintaining this layout keeps the system modular and clear, enabling the AI to handle debugging recall, multi-agent workflows, code modifications, and knowledge queries without confusion.

**Last Updated:** February 2025  
**Maintained By:** AI Recall System
