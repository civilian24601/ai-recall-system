# Project Vision: Self-Learning AI Building Engine

## Overview
A local, autonomous AI system that builds, iterates, and improves projects—starting with tools/apps, scaling to SaaS—via a front-end UI for prompts. A "kernel" MVP that self-develops, refactors, tests, and learns, spinning up structurally identical project instances with nested Chroma collections, feeding a `global_knowledge_base` for cross-project intelligence.

## Goals
- **MVP**: Self-building app—autonomous feature adds, refactoring, regression-free, full-project awareness via Chroma.
- **Scale**: SaaS-level projects—robust, UI-driven, leveraging `global_knowledge_base`.
- **Learning**: Logs (BELogs, debug) and blueprints drive self-correction, error avoidance, and efficiency.

## Architecture
- **Project Template**: Each `/mnt/f/projects/[project_name]` gets:
  - `[project_name]_project_codebase`, `[project_name]_knowledge_base`, etc.
  - Scripts: `index_*.py`, `blueprint_execution.py`, `agent.py`.
- **Global Brain**: `global_knowledge_base` aggregates logs, blueprints, successes/failures across projects.
- **Front-End**: UI (TBD in `/frontend`) for prompts and oversight.

## Milestones
1. **MVP**: App builds itself (e.g., basic CRUD tool)—RAG, blueprints, testing solid.
2. **Multi-Project**: Two projects share `global_knowledge_base`.
3. **UI**: Prompt-driven iteration.

## Why?
- Ownership over Cursor/LLM APIs—local, cost-free, custom, future-proof, layer 1 memory architecture in anticipation of AI acceleration and AGI. A billion-dollar tool for the plebs.
- Nested DBs for a solopreneur’s memory palace—smarter with every project.

Last Updated: March 04, 2025