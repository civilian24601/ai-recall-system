# 🌟 Roadmap for AI Recall System

## 🌱 Overview

This roadmap tracks the development of the AI Recall System—a self-learning, local AI kernel for solopreneurs. Current as of March 4, 2025.

## 🚀 Phase 1: Foundation (In Progress)

- **Goal**: Build indexing backbone for code and knowledge.
- **Status**:
  - `index_codebase.py`: Indexes `/code_base/`, `/scripts/`, `/tests/`, `/frontend/` (110 chunks in `project_codebase`).
    - Line-based chunking (300 lines, 50 overlap), watchers active, logs to `/logs/script_logs/index_codebase.log`.
  - `index_knowledgebase.py`: Indexes `/knowledge_base/` and `/agent_knowledge_bases/` (266 chunks in `knowledge_base`).
    - Header-based chunking (~500 chars), dedup by mtime/hash, logs to `/logs/script_logs/index_knowledgebase.log`.
- **Next**:
  - [ ] Polish `index_knowledgebase.py` test mode (Issue #5).
  - [ ] Separate test/prod data (Issue #3).

## 🤖 Phase 2: Agent System (Next)

- **Goal**: Autonomous agents querying Chroma for debugging and iteration.
- **Tasks**:
  - [ ] Stub `agent.py` (engineer: query `project_codebase`, propose fixes).
  - [ ] Stub `agent_manager.py` (reviewer: validate, commit fixes).
  - [ ] Blueprint in `blueprints/agent_blueprint_v1.json`.
- **Milestone**: Basic RAG loop (query, fix, log), handling timeouts (Issue #4).

## 💰 Phase 3: Tool Deployment

- **Goal**: Ship a sellable endpoint tool (TBD—first project TBD by Alex).
- **Tasks**:
  - [ ] Package a retrieval script (e.g., `retrieve_codebase.py`) as CLI.
  - [ ] Test retrieval on `project_codebase` (110 chunks) and `knowledge_base` (266 chunks).
- **Milestone**: First revenue (~Q2 2025)—project TBD.

## 🌐 Phase 4: Multi-Project Scaling

- **Goal**: Kernel templates spawn projects sharing `global_knowledge_base`.
- **Tasks**:
  - [ ] Define project template (`/mnt/f/projects/[project_name]/*`).
  - [ ] Aggregate logs/blueprints into `global_knowledge_base`.
- **Milestone**: Two projects sync data.

## 🖼️ Phase 5: UI and SaaS

- **Goal**: Front-end UI for prompts, scale to SaaS.
- **Tasks**:
  - [ ] Build `/frontend/` UI (Next.js, TypeScript).
  - [ ] Subscription model ($20/month).
- **Milestone**: UI-driven iteration (Q3-Q4 2025).

## 📊 Current State (03/04/2025)

- **Indexing**:
  - Code: 105 files, 110 chunks (`project_codebase`).
  - Knowledge: 25 files, 266 chunks (`knowledge_base`).
- **Logging**: Scripts log to `/logs/script_logs/`.
- **Pending**: Agent stubs, test/prod split, doc updates (Issue #1).

## 🌌 Long-Term Vision

- **Memory Palace**: Evolve `global_knowledge_base` into a solopreneur’s cross-project brain—a living, traversable archive of every script, fix, blueprint, and lesson. Think a nested, pristine Chroma ecosystem where each project’s `knowledge_base`, `project_codebase`, and logs feed a central intelligence that grows smarter with every commit.
- **Autonomy**: Self-building apps that spin up from templates, refactor themselves, and iterate without human nudging. Agents become a “city of workers”—engineers, reviewers, planners—collaborating via blueprints, executing at a tempo, and spawning tools or SaaS that fund the next leap.
- **Impact**: A billion-dollar toolkit for plebs—local, cost-free, custom, and future-proof. Passive income streams stack as the kernel births projects (e.g., micro-tools, niche SaaS), each leveraging past wins. A solopreneur’s force multiplier, scaling from one coder to an AI-driven empire.

Last Updated: March 4, 2025
