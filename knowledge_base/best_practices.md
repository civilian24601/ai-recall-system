🌟 AI Best Practices - AI Recall System

🌱 Overview
This doc lays out the best practices for AI-generated code, debugging recall, and workflow execution in the AI Recall System. It’s all about keeping things tight, scalable, and self-improving as we roll from manual tweaks to full-on AI autonomy—376 chunks (110 code, 266 docs) and counting as of March 4, 2025.

🚀 Primary Goals:

✅ Ensure AI sticks to structured, efficient workflows—no chaos allowed.
✅ Standardize AI code for readability, reusability, maintainability—clean and lean.
✅ Optimize debugging recall and execution—no reinventing the wheel.
✅ Push AI to self-improve and execute with robust safety nets.

🛠️ 1. AI Code Generation Best Practices

📌 All AI-generated code must be structured, maintainable, and reusable—no spaghetti here.

🔧 AI Code Formatting Standards
✅ Use snake_case for vars and functions—e.g., fetch_recent_debug_logs.
✅ Every function gets a docstring—clear purpose, args, returns, no excuses.
✅ Keep it modular—small, focused functions over bloated monsters.
✅ No redundancy—AI checks Chroma (project_codebase, 110 chunks) before spinning new code.

🌟 Example AI-Generated Code:

Imagine a function fetch_recent_debug_logs(limit: int = 5) -> list. It’s got a docstring: “Retrieves the latest debugging logs from ChromaDB. Args: limit (int) - number of logs. Returns: list of entries.” It queries chroma_db/—clean, documented, and pulls from our 376-chunk memory vault.

🐞 2. AI Debugging & Execution Best Practices

📌 AI debugging recall and execution follow a strict playbook—structured, smart, no guesswork.

🔍 AI Debugging Workflow
✅ Step 1: AI digs into Chroma first—e.g., 110 code chunks in project_codebase—before dreaming up fixes.
✅ Step 2: Prioritizes past wins—fixes that stuck, logged in /logs/script_logs/.
✅ Step 3: Ranks solutions by confidence and context—e.g., 98% hit rate on a schema fix.
✅ Step 4: Suggests or applies the top fix—human nudge now, AI hands soon.

🌟 Example Debugging Run:

You type ai-debug "Show last 3 debugging sessions." AI spits back: “Debug Log 2025-03-04: Error - Mid-chunk cut in agent.py. Fix Suggested - Bump chunk size to 500 lines. Confidence: 85%.” It’s pulling from knowledge_base (266 chunks)—no repeat flops.

📚 3. AI Knowledge Retrieval & ChromaDB Best Practices

📌 AI retrieval is all about accuracy, relevance, and clean storage—376 chunks live, more coming.

📖 AI Query Execution Guidelines
✅ AI hits Chroma first—e.g., retrieve_codebase.py "error handling" scans 110 code chunks.
✅ Ranks by success—past fixes sorted, top picks bubble up.
✅ Logs every grab—e.g., /logs/script_logs/index_knowledgebase.log tracks “Indexed 266 chunks”.

🌟 Example Query:

A function retrieve_past_solution(query: str) -> list—docstring says: “Queries ChromaDB for past fixes. Args: query (str) - issue desc. Returns: list of ranked solutions.” It pulls from project_codebase—e.g., “try/except from agent.py, 90% confidence.”

🔄 4. AI Self-Refactoring & Code Optimization Best Practices

📌 AI refactoring keeps it efficient, performance-smart, and lean—no bloat, no breakage.

🛠️ AI Code Optimization Workflow
✅ AI compares past wins—e.g., 266 chunks in knowledge_base for best practices.
✅ Refactors for speed—streamlines without gutting logic—e.g., deduped README.md (Issue #4).
✅ Validates with tests—checks against test_index_codebase.py before committing.

🌟 Example Refactor Check:

A function validate_refactored_code(old_code: str, new_code: str) -> bool—docstring: “Validates refactored code. Args: old_code, new_code (str). Returns: bool - True if better.” It flags if new code bloats 20% over old—keeps AI honest.

🛡️ 5. AI Execution & Oversight Best Practices

📌 AI execution stays safe and validated—no rogue moves on our 376-chunk empire.

🔒 AI Execution Safety Guidelines
✅ Human OK needed for big changes—e.g., overwriting agent.py.
✅ Logs all moves—e.g., /logs/script_logs/ tracks “Re-indexed 110 chunks”.
✅ Checks past success—e.g., only suggests fixes with 85%+ hit rate from Chroma.

🌟 Example Guardrail:

A function ai_execution_guardrail(modification: str) -> bool—docstring: “Validates AI mods. Args: modification (str). Returns: bool - True if safe.” It scores risk—under 10, it’s a go. Keeps our system tight.

🌟 General Coding Guidelines
✅ Language: Python 3.10+ for scripts (index_codebase.py), TypeScript for /frontend/.
✅ Style: PEP 8 for Python, Prettier for TS/JS—lines under 80 chars where sane.
✅ Comments: Docstrings everywhere, inline notes for tricky bits—e.g., chunk_file().
✅ Errors: Try/except on file ops, Chroma calls—log to /logs/script_logs/.

📜 Script Development
✅ Modularity: Split logic—e.g., chunk_file(), get_file_hash() in index_codebase.py.
✅ Config: Constants up top—e.g., CHROMA_PATH, CHUNK_SIZE_DEFAULT = 300.
✅ Execution: One-shot or watchers—e.g., python index_codebase.py --watch.

📝 Logging
✅ Where: /logs/script_logs/<script>.log—e.g., index_knowledgebase.log.
✅ How: logging module, format %(asctime)s - %(levelname)s - %(message)s.
✅ Levels:

INFO: “Indexed 105 files, 110 chunks”.
WARNING: “Root dir /tests/ not found”.
ERROR: “Failed to read agent.py”.

🌟 Example:
“import logging; LOG_FILE = '/mnt/f/projects/ai-recall-system/logs/script_logs/index_codebase.log'; logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s'); logger.info('Connecting to Chroma...')”

✂️ Chunking Strategies
✅ Code Files (index_codebase.py):

Line-based, 300 lines/chunk, 50-line overlap—110 chunks live.
.py, .js, .tsx—no .md or .json.
Metadata: start_line, end_line, function_name (empty sans AST), class_name, node_type.
✅ Markdown Files (index_knowledgebase.py):
Header-based, ~500 chars/chunk, split by #—266 chunks live.
Dedup via mtime, SHA-256—newest wins.
Metadata: filename, chunk_index, total_chunks, source, mtime, hash.

👀 Watchers
✅ Why: Real-time indexing—create, modify, move, delete.
✅ How: watchdog, 2-sec debounce—e.g., index_codebase.py --watch.
✅ What: Monitors /code_base/, /scripts/, /tests/, /frontend/.
✅ Rules: Skip node_modules, dist, chroma_db—re-index on change, trash old chunks on delete.

📡 ChromaDB Usage
✅ Collections:
-project_codebase: 110 chunks (code).
-knowledge_base: 266 chunks (docs).
-_test: E.g., knowledge_base_test (241 chunks).

✅ Path: /mnt/f/projects/ai-recall-system/chroma_db/.
✅ Embeddings: sentence-transformers/all-MiniLM-L6-v2.

📦 Commit Practices
✅ Tags: [SCRIPT], [DOC], [TEST], [FIX]—e.g., [SCRIPT] index_codebase.py: added logging.
✅ Messages: What + why—e.g., “Added 110chunks to project_codebase”.
✅ Branch: dev—always.

🧪 Testing
✅ Unit Tests: /tests/—e.g., test_index_codebase.py, ephemeral test_chroma_db/.
✅ Validation: inspect_collections.py—e.g., 110 docs in project_codebase.
✅ Refer to testing_plan.md and TEST_SCENARIOS.md

📚 Documentation
✅ When: Update with big shifts—e.g., logging to /logs/script_logs/.
✅ Where: /knowledge_base/ for core, /agent_knowledge_bases/ for agent READMEs.

🌟 Updates
🚫 Avoid Redundant Endpoint Detection
✅ Unify LLM/Flask logic—e.g., shared module over dupe code in user_interaction_flow.py.

📝 Logging Consistency
✅ Standardize naming—e.g., merge log_work_session.py, work_session_logger.py into one.

🌐 Single network_utils
✅ One detect_api_url()—e.g., shared across generate_work_summary.py, no repeats.

🌟 Summary
✅ Code: Structured, reusable—snake_case, docstrings, modular.

✅ Debugging: Recall-first—Chroma queries, ranked fixes.

✅ Retrieval: Smart, logged—376 chunks, growing.

✅ Refactoring: Lean, validated—past wins guide.

✅ Execution: Safe, tracked—guardrails rule.

📅 Last Updated: March 4, 2025

🔹 Maintained by: AI Recall System
