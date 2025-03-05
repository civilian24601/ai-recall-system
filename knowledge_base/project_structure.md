# 📂 Project Structure: AI Recall System

## 🌟 Overview

This outlines the AI Recall System’s directory and collection structure as of March 4, 2025, supporting a self-learning kernel.

## 🗂️ Root Directories

- **/code_base/**: Core code (e.g., `agent.py`)—105 files, 110 chunks in `project_codebase`.
- **/scripts/**: Indexing scripts (e.g., `index_codebase.py`, `index_knowledgebase.py`).
- **/tests/**: Test scripts and mock data (e.g., `test_index_codebase.py`).
- **/frontend/**: UI experiments (e.g., `page.tsx`)—part of `project_codebase`.
- **/knowledge_base/**: Core docs (e.g., `workflow.md`)—25 files, 266 chunks in `knowledge_base`.
- **/agent_knowledge_bases/**: Agent READMEs—indexed into `knowledge_base`.
- **/chroma_db/**: Chroma storage (`project_codebase`: 110, `knowledge_base`: 266).
- **/logs/**:
  - **/script_logs/**: Script runtime logs (e.g., `index_codebase.log`).
- **/blueprints/**: Agent blueprints (TBD, e.g., `agent_blueprint_v1.json`).

## 📡 Chroma Collections

- **project_codebase**: 110 chunks (code: `.py`, `.js`, `.tsx`).
- **knowledge_base**: 266 chunks (markdown from `/knowledge_base/`, `/agent_knowledge_bases/`).
- **_test**: Test variants (e.g., `knowledge_base_test`: 241 chunks).
- **Future**: `execution_logs`, `blueprint_versions`, etc., per project.

## 🌱 Future Structure

- **/mnt/f/projects/[project_name]/**:
  - `[project_name]_project_codebase`
  - `[project_name]_knowledge_base`
  - Uniform collections: `execution_logs`, `debugging_logs`, etc.
- **/global_knowledge_base/**: Cross-project brain.

Last Updated: March 4, 2025
