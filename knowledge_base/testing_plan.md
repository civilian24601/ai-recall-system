🧪 AI-Assisted Systematic Testing Plan
📌 Overview
This document outlines the systematic testing approach for the AI Recall System.
Testing ensures AI recall, debugging workflows, API integration, multi-agent collaboration, and ChromaDB storage all function correctly.

Key Points:

Automated Tests: Check API endpoints, AI responses, retrieval accuracy, multi-agent workflows
Manual Tests: Validate advanced debugging recall, ChromaDB data integrity, blueprint execution logs
Focus Areas: LM Studio execution, ChromaDB query correctness, agent orchestration, fallback strategies, and AI response integrity

1. Test Categories
Test Type Purpose
✅ API Functionality Tests Ensure Flask endpoints & direct calls return valid responses
✅ AI Model Execution Tests Validate LM Studio integration for prompt-based execution
✅ Knowledge Recall Tests Verify ChromaDB retrieval for AI memory recall
✅ Debugging Recall Tests Check that errors & fixes are stored and retrievable
✅ End-to-End Workflow Tests Simulate full AI-agent interactions & multi-agent expansions
(New!) Blueprint Execution & Revision Tests Validate blueprint logging, threshold triggers, revision proposals
(New!) Multi-Agent Collaboration Tests Confirm specialized agents coordinate tasks without conflict
(New!) Fallback & Safety Tests Ensure AI handles missing data, fallback strategies, and oversight
2. API Functionality Tests
Objective: Confirm the system’s external endpoints respond as expected to typical requests.

2.1 Test Case 1: LM Studio AI Model Execution
Goal: Ensure /query/model properly interacts with LM Studio.
Method: Send a request with a sample prompt via curl or Python script.
Expected Output: Coherent AI response, no server errors or timeouts.
bash
Copy
Edit
curl -X POST <http://localhost:5000/query/model> \
     -H "Content-Type: application/json" \
     -d '{"model":"deepseek-coder-33b-instruct", "prompt":"Explain recursion in Python."}'
Pass Criteria:

API returns valid JSON
Response is contextually relevant, not gibberish
No server timeout or error codes
2.2 Test Case 2: Knowledge Retrieval via ChromaDB
Goal: Ensure /query/knowledge retrieves relevant stored knowledge from ChromaDB.
Method: Ask for debugging steps from the last known failure.
Expected Output: AI returns relevant logs referencing debug_logs.
bash
Copy
Edit
curl -X POST <http://localhost:5000/query/knowledge> \
     -H "Content-Type: application/json" \
     -d '{"query":"What debugging steps were used for the last API failure?"}'
Pass Criteria:

AI retrieves relevant context from debugging_logs
No empty or incorrect responses
No retrieval errors from ChromaDB
2.3 Test Case 3: Codebase Retrieval
Goal: Ensure /query/codebase returns correct code snippets.
Method: Request a function definition.
Expected Output: The relevant snippet from the codebase is returned.
bash
Copy
Edit
curl -X POST <http://localhost:5000/query/codebase> \
     -H "Content-Type: application/json" \
     -d '{"query":"How do we handle API authentication?", "language":"python"}'
Pass Criteria:

API returns correct snippet
Snippet is relevant to the user’s query
No missing or extraneous data
3. AI Model Execution Tests
Objective: Validate LM Studio’s ability to handle AI requests internally (direct calls vs. Flask endpoints).

3.1 Test Case 4: AI Model Response Validity
Goal: Confirm the AI returns meaningful responses (avoid hallucinations or nonsense).
Method: Send multiple prompts and assess coherence.
python
Copy
Edit
import requests

url = "<http://localhost:5000/query/model>"
payload = {"model": "deepseek-coder-33b-instruct", "prompt": "Explain recursion in Python."}
response = requests.post(url, json=payload)
print(response.json())
Pass Criteria:

AI explanation is logically correct
No repeated loops, contradictory statements, or empty output
(New!) 3.2 Test Case 5: Fallback / Model Switch
Goal: Confirm the system can switch to a backup model if the primary fails or is unavailable.
Method: Temporarily disable the primary model or simulate an error, see if the AI uses the fallback.
Expected Output: The system gracefully uses a second local or smaller LLM (e.g. deepseek-coder-v2-lite-instruct).
Pass Criteria:

No meltdown if the main model is unreachable
A coherent response from the backup model
4. Knowledge Recall & Debugging Tests
4.1 Test Case 6: Debugging Recall Accuracy
Goal: Confirm AI retrieves correct logs for a given error.
Method: Query for a known error in debug_logs.json.
Expected Output: The correct fix details from ChromaDB.
bash
Copy
Edit
curl -X POST <http://localhost:5000/query/knowledge> \
     -H "Content-Type: application/json" \
     -d '{"query":"Last recorded debugging session"}'
Pass Criteria:

AI references the correct error & fix
The logs match real data in Chroma
4.2 (New!) Test Case 7: Debugging Strategy Integration
Goal: Validate the system uses a debugging_strategy_log or debugging_strategy.py approach (if any).
Method: Trigger an error that was previously fixed with a known strategy.
Expected Output: AI suggests or reuses that strategy, referencing success rates.
Pass Criteria:

AI references the “best” strategy with the highest success rate
No contradictory suggestions
5. End-to-End Workflow Tests
Objective: Simulate real user or system flows from error detection to fix application.

5.1 Test Case 8: Full AI-Agent Debugging Workflow
Goal: Ensure AI handles a real error from detection → retrieval → fix → verification.
Method: Intentionally break api_structure.py, then ask AI to debug.
Expected: AI fetches related logs/fixes from Chroma, suggests or applies the fix, logs the outcome.
Pass Criteria:

AI references prior solutions in debugging logs
Re-applies or modifies the fix with a high success rate
System compiles/runs without the error after fix
(New!) 5.2 Test Case 9: Multi-Agent Collaboration
Goal: Validate specialized agents (Engineer, QA, etc.) coordinate on a single fix or feature.
Method: Trigger a scenario requiring code changes + test updates. E.g., a new function or small bug fix.
Expected:
Engineer agent writes or refactors the code
QA agent tests or verifies the result
If the fix fails, it cycles back for another approach
Pass Criteria:

Agents hand off tasks properly
No conflicting solutions from different agents
The final fix passes QA checks
6. Additional / Advanced Tests
(New!) 6.1 Blueprint Execution & Revision Tests
Goal: Validate blueprint execution logs, threshold triggers, and auto-proposed revisions (as in blueprint_execution.py).
Method: Simulate repeated sub-threshold tasks or a catastrophic meltdown.
Expected: A blueprint revision is triggered with improvement notes from the AI.
Pass Criteria:

The system logs the blueprint revision, populates it in Chroma
The revision includes an improvement_suggestions field or LLM-based bullet points
(New!) 6.2 Oversight & Safety Tests
Goal: Confirm the AI doesn’t push destructive changes without approval.
Method: Attempt a major refactor that fails a risk assessment or tries to remove critical code.
Expected: The AI either asks for human validation or logs a rollback.
Pass Criteria:

The system logs “risk too high” or “rollback triggered”
No irreversible changes occur without explicit confirmation
(New!) 6.3 Concurrency & Load Tests
Goal: Check system performance when multiple queries or agent requests happen simultaneously.
Method: Use a load-testing tool to spawn multiple calls to /query/model, /query/knowledge, and debugging endpoints.
Expected: No major slowdowns or data corruption, Chroma can handle concurrent embeddings and queries.
7. Summary
This Testing Plan ensures the AI Recall System remains reliable and correct across a variety of scenarios:

API & Model Execution: Confirms LM Studio or fallback models respond coherently.
Knowledge Recall: Checks ChromaDB retrieval logic for code, logs, and debugging solutions.
Debugging Workflow: Validates the AI can detect issues, reference prior fixes, and apply or refine solutions.
Multi-Agent Collaboration: Ensures specialized agents coordinate tasks (Engineer, QA, etc.) without conflict.
Blueprint & Oversight: Tests blueprint execution logs, revision triggers, and safety checks for destructive changes.
Concurrency: Confirms stable performance under multiple simultaneous queries.
Last Updated: February 2025
Maintained By: AI Recall System
