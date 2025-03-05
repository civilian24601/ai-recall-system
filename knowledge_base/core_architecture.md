# 🏗️ Core Architecture - AI Recall System

## 📌 Overview

The AI Recall System is a **self-improving AI-powered development assistant** evolving from **manual AI-assisted recall to fully autonomous debugging and execution workflows**. It’s built to be a local, solopreneur-driven kernel—scalable, cost-free, and custom—rooted in a persistent memory backbone.

✅ **Primary Capabilities**:  

- **AI Knowledge Recall**: Retrieves past work, debugging logs, and solutions from ChromaDB.  
- **Self-Debugging & Execution**: Detects errors, fetches fixes, and applies them autonomously.  
- **Autonomous Code Generation**: Iterates on code improvements with minimal human input.  
- **Multi-Agent Collaboration (Future)**: Teams of AI agents optimize and execute workflows.  

🚀 **Current Status (03/04/2025)**: Single-Agent Mode in progress—indexing complete, agents next.  
📌 **Next Step**: Automate self-debugging, expand to multi-agent workflows.

---

## 📌 System Components

| **Component** | **Purpose** |
|---------------|-------------|
| **Flask API (`api_structure.py`)** | Routes AI queries, model execution, and debugging requests (TBD). |
| **LM Studio (Local Models)** | Executes AI-generated prompts & suggestions (planned integration). |
| **ChromaDB (`chroma_db/`)** | Stores vector embeddings of past work—110 chunks in `project_codebase`, 266 in `knowledge_base`. |
| **Continue.dev (VS Code AI Assistant)** | Enhances real-time AI-powered development (optional tool). |
| **CLI Commands (`ai-recall`, `ai-debug`)** | Manual recall/debugging—evolving to agent-driven (TBD). |
| **Knowledge Base (`knowledge_base/`)** | Docs, architecture notes, history—25 files, 266 chunks indexed. |

✅ **Current Setup**:  

- **ChromaDB**: Persistent at `/mnt/f/projects/ai-recall-system/chroma_db/`, using `sentence-transformers/all-MiniLM-L6-v2`.  
- **Indexing**: `index_codebase.py` (line-based, 300 lines, 50 overlap), `index_knowledgebase.py` (header-based, ~500 chars).  
- **Logging**: `/logs/script_logs/<script>.log` (e.g., `index_codebase.log`) with `INFO`, `WARNING`, `ERROR`.

---

## 📌 Single-Agent Mode (Current State)

📌 **Current Operation**:  
✅ AI retrieves past debugging logs, work summaries, and solutions from ChromaDB.  
✅ Assists debugging but requires human execution of fixes.  
✅ Does not yet refactor or apply fixes automatically.  

🔹 **Workflow**:  
1️⃣ User asks AI a recall question via CLI (`retrieve_codebase.py`) or VS Code.  
2️⃣ AI queries ChromaDB (`project_codebase`: 110 chunks, `knowledge_base`: 266 chunks).  
3️⃣ AI suggests solutions based on indexed logs/docs.  
4️⃣ User applies fixes manually, updates knowledge base via commits.  

✅ **Stats (03/04/2025)**:  

- **Code**: 105 files indexed, 110 chunks—`.py`, `.js`, `.tsx` from `/code_base/`, `/scripts/`, `/tests/`, `/frontend/`.  
- **Docs**: 25 `.md` files, 266 chunks from `/knowledge_base/` and `/agent_knowledge_bases/`.  
- **Logging**: Timestamped in `/logs/script_logs/`—e.g., “Processed 105 files, 110 chunks”.

---

## 📌 Multi-Agent Mode (Future Expansion)

📌 **Vision**: Scale to a multi-agent framework where AI transitions from passive recall to active execution and optimization.  

### 🔹 Planned AI Agents

| **Agent** | **Role** |
|-----------|----------|
| **Engineer Agent** | Writes, refactors, and improves code—queries `project_codebase`. |
| **QA Agent** | Tests modifications for accuracy—validates against `knowledge_base`. |
| **Debug Agent** | Detects errors, retrieves fixes, applies them—logs to `execution_logs`. |
| **Oversight Agent** | Monitors behavior, prevents errors, manages ChromaDB consistency. |
| **DevOps Agent** | Handles scaling, infrastructure—syncs to `global_knowledge_base`. |

✅ **Goal**: A self-improving system—agents collaborate via blueprints (e.g., `/blueprints/agent_blueprint_v1.json`).

---

## 📌 AI Self-Debugging & Knowledge Storage

📌 **Transition**: From manual assistance to autonomous execution.  

### 🔹 Current Debugging Process

1️⃣ AI logs issues manually via user commits—no `debug_logs.json` yet.  
2️⃣ AI retrieves fixes from ChromaDB when prompted (e.g., `retrieve_codebase.py "error handling"`).  
3️⃣ AI suggests solutions—user applies them.  

### 🔹 Future Self-Debugging

✅ AI detects errors in real-time (watchers in `index_codebase.py`).  
✅ Queries past solutions from `debugging_logs` (TBD collection).  
✅ Applies fixes post-verification by QA agent, logs outcomes to `execution_logs`.  

🚀 **Goal**: Closed-loop debugging—minimal human input.

---

## 📌 AI Knowledge Flow (ChromaDB-Powered Recall)

📌 **ChromaDB**: AI’s long-term memory—persistent, scalable.  
✅ Updates with every run (`index_*.py`), queried before new solutions.  
✅ Stores project-specific context—code, docs, logs.  

### 🔹 Knowledge Retrieval Workflow

1️⃣ AI searches ChromaDB before generating fixes—e.g., 110 code chunks, 266 doc chunks.  
2️⃣ Retrieves relevant past work (e.g., `agent.py` chunk with try/except).  
3️⃣ Ranks solutions by relevance—uses embeddings (`all-MiniLM-L6-v2`).  
4️⃣ Applies best fix or generates/tests new one if none exist.  
5️⃣ Logs results to Chroma—e.g., `execution_logs` (TBD).

🚀 **Goal**: Avoid reinventing the wheel—recall first, innovate second.

---

## 📌 Future Goals & Milestones

| **Phase** | **Goal** | **AI Capability** |
|-----------|----------|-------------------|
| **Phase 1: AI Recall & Debugging** | ✅ Store & retrieve past work—110 + 266 chunks indexed. | Passive recall only. |
| **Phase 2: AI Self-Debugging** | ✅ Apply past fixes automatically. | Self-executing resolution. |
| **Phase 3: AI Self-Refactoring** | ✅ Modify & improve code autonomously. | Optimization loops. |
| **Phase 4: Fully Autonomous AI** | ✅ Execute full projects. | Human oversight only. |

🚀 **Endgame**: An autonomous, self-improving dev assistant—local, relentless, yours.

---

## 📌 Summary

📌 **This covers**:  
✅ Current single-agent recall (110 code, 266 doc chunks).  
✅ Planned multi-agent expansion—engineer, QA, debug roles.  
✅ ChromaDB memory—`/chroma_db/`, logging in `/logs/script_logs/`.  
✅ Future autonomy—self-debugging to full execution.  

📅 **Last Updated**: March 4, 2025  
🔹 **Maintained by**: AI Recall System Team
