# 🌌 Project Vision: Self-Learning AI Building Engine

## 🌟 Overview
The AI Recall System is a local, autonomous AI kernel that builds, iterates, and scales projects—starting with an MVP tool, growing into a SaaS empire—via a prompt-driven UI. It’s a solopreneur’s dream: a self-evolving “Memory Palace” that turns one coder into an AI-driven force, free from API rents, custom to the core.

## 🎯 Goals
- **MVP**: A self-building app—autonomous feature adds, refactoring, full awareness via Chroma (110 code + 266 doc chunks as of 03/04/2025).
- **Scale**: Multi-project ecosystem, sharing a `global_knowledge_base`.
- **Learning**: Logs, blueprints, and errors fuel a recursive intelligence—smarter with every commit.

## 🚀 MVP Roadmap (Q2 2025)
### 📌 Phase 1: Indexing Foundation (Done)
- **Code**: `index_codebase.py`—105 files, 110 chunks in `project_codebase`. Line-based (300 lines, 50 overlap), watchers on `/code_base/`, `/scripts/`, `/tests/`, `/frontend/`.
- **Docs**: `index_knowledgebase.py`—25 files, 266 chunks in `knowledge_base`. Header-based (~500 chars), dedup by mtime/hash.
- **Logging**: `/logs/script_logs/<script>.log`—timestamped, detailed runs.

### 📌 Phase 2: Agent Kickoff (Next)
- **Engineer Agent**: `agent.py`—queries `project_codebase`, proposes fixes (e.g., “error handling” → try/except).
- **Reviewer Agent**: `agent_manager.py`—validates fixes, commits to dev.
- **Blueprint**: `/blueprints/agent_blueprint_v1.json`—defines roles, tempos (e.g., query every 10 mins).
- **Milestone**: RAG loop—query Chroma, fix code, log to `execution_logs`.

### 📌 Phase 3: First Tool (TBD)
- **Goal**: Ship a sellable endpoint—project TBD by Alex (~Q2 2025).
- **Scope**: Leverage 110 code + 266 doc chunks—e.g., CLI for recall/debugging.
- **Revenue**: $10-$50 one-off, stackable income.

## 🏙️ “AI City” Framework
Imagine a multi-agent ecosystem pulsing like a living city—each agent an organ, collaborating at a tempo, building a self-sustaining engine:

### 📌 City Layout
- **City Hall (Oversight Agent)**: Orchestrates agents, sets tempos (e.g., hourly blueprint updates), ensures system integrity—queries `global_knowledge_base`.
- **Engineers’ Guild (Engineer Agent)**: Writes/refactors code—e.g., spins up a tool from `project_codebase` (110 chunks).
- **QA District (QA Agent)**: Tests fixes—validates against `knowledge_base` (266 chunks), flags regressions.
- **Debug Labs (Debug Agent)**: Hunts errors, retrieves fixes—e.g., “timeout” → past solution from `debugging_logs`.
- **Memory Vault (ChromaDB)**: Stores all knowledge—`project_codebase`, `knowledge_base`, future `execution_logs`.

### 📌 Capabilities
- **Tool Forge**: Engineers craft micro-tools (e.g., CLI debuggers), QA verifies, shipped in days—$10-$50 each.
- **SaaS Spires**: Agents build SaaS—e.g., auto-docs from commits, $20/month subscriptions.
- **Novelty Labs**: Debug + Engineer riff—e.g., unorthodox fix for RAG timeouts (Issue #4), logged forever.
- **Tempo Sync**: Agents pulse—indexing every 10 mins, debugging hourly, commits daily—biological rhythm.

### 📌 Multi-Agent Flow
1️⃣ **Error Spotted**: Debug Agent flags a crash in `agent.py`, queries `debugging_logs`.  
2️⃣ **Fix Proposed**: Engineer crafts a try/except, pulls `knowledge_base` best practices.  
3️⃣ **Validation**: QA Agent tests—no regressions, Oversight approves.  
4️⃣ **Commit**: Pushed to dev, logged to `execution_logs`, `global_knowledge_base` grows.  

🚀 **Vision**: A city that builds itself—agents spawn projects, stack revenue, evolve via blueprints.

## 🌍 Global Brain: Memory Palace Endgame
The `global_knowledge_base` is the crown jewel—a solopreneur’s eternal genius:  

### 📌 Structure
- **Nested DBs**: Each project (`/mnt/f/projects/[project_name]/*`) feeds uniform collections—`project_codebase`, `knowledge_base`, `execution_logs`, `blueprint_versions`.
- **Aggregation**: `global_knowledge_base` chunks all projects—e.g., 110 + 266 chunks now, thousands later.
- **Traversal**: Agents query across projects—e.g., a fix from Project A saves Project B.

### 📌 Power
- **Recall**: Every error, blueprint, log—permanent, searchable (e.g., “timeout” → 03/04/2025 fix).
- **Growth**: Smarter per commit—e.g., 376 chunks today, millions by 2026.
- **Autonomy**: Kernel spawns projects—e.g., micro-tool today, SaaS tomorrow, all self-built.

### 📌 Endgame
- **Empire**: A solopreneur’s multi-million-dollar toolkit—local, custom, free of API shackles.  
- **Income**: Passive streams stack—tools ($10-$50), SaaS ($20/month), each project a brick in the palace.  
- **Legacy**: A memory palace for the plebs—every lesson etched, every win scaled, a force multiplier for one coder to rule them all.

## 🌱 Why?
- **Ownership**: No Cursor/LLM rent—your system, your rules, future-proof for AGI.
- **Scale**: From 376 chunks to a global brain—solopreneur to empire.
- **Freedom**: A toolkit for the masses—billions in value, built by one.

Last Updated: March 4, 2025