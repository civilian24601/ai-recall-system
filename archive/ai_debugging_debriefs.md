# 📄 AI Debugging Debrief Format  

## **📌 Overview**

This document defines the **standardized debugging debrief process** used by the AI Recall System.  

🚀 **Primary Goals:**  
✅ **Ensure AI logs debugging issues, solutions, and outcomes consistently.**  
✅ **Enable AI to retrieve past debugging sessions from ChromaDB.**  
✅ **Allow AI to refine its problem-solving methods over time.**  

📌 **AI debugging debriefs ensure system self-improvement and prevent repeated troubleshooting cycles.**  

---

## **📌 1. AI Debugging Workflow**  

📌 **AI follows a structured workflow when debugging issues:**  

| **Stage** | **Process** |
|-----------|------------|
| **Stage 1: Error Detection** | AI detects failure & logs details into `debug_logs.json`. |
| **Stage 2: Debugging Recall** | AI queries ChromaDB (collection="debugging_logs") for past debugging attempts. |
| **Stage 3: Solution Suggestion** | AI suggests the most relevant past fix. |
| **Stage 4: Fix Execution** | AI applies or recommends a fix (depending on user preference). |
| **Stage 5: Validation & Learning** | AI evaluates the success of the applied fix and updates knowledge. |

🚀 **Goal:** AI **retrieves and applies past solutions before generating new debugging workflows.**  

---

## **📌 2. AI Debugging Log Format**  

📌 **AI stores debugging logs in `debug_logs.json` for retrieval & analysis.**  

### **🔹 Standard Debugging Log Entry**  

```json
{
    "timestamp": "2025-02-10 14:23:11",
    "error": "SQL Integrity Constraint Violation",
    "stack_trace": "File 'db_handler.py', line 42, in execute_query...",
    "fix_attempted": "Added unique constraint to the schema.",
    "fix_successful": true,
    "ai_confidence_score": 0.95
}
✅ Ensures debugging logs capture issue details, attempted solutions, and success rates.

📌 3. AI Debugging Retrieval & Solution Matching
📌 AI queries ChromaDB to retrieve past debugging sessions before generating new fixes.

🔹 ChromaDB Debugging Query Example

def retrieve_debugging_logs(error_message: str) -> list:
    """
    Queries ChromaDB for past debugging logs related to the given error message.

    Args:
        error_message (str): Error description to search for.

    Returns:
        list: Matching debugging log entries.
    """
    query = f"SELECT * FROM debug_logs WHERE error LIKE '%{error_message}%'"
    return query_chroma_db(query)
✅ Allows AI to reuse past debugging attempts instead of starting from scratch.

📌 4. AI Debugging Debrief Template
📌 AI automatically generates a debugging debrief after resolving an issue.

🔹 Standard AI Debugging Debrief Format
🔹 Task Name: [Brief Description of Debugging Task]
🔹 Files Modified: [List of modified files]
🔹 Functions Edited: [List of changed functions]
🔹 Error Logs: [Stack trace & debugging details]
🔹 AI Debugging Summary: [Steps taken, solutions attempted, and failures encountered]

✅ Ensures AI debugging memory is structured and retrievable for future reference.

📌 5. AI Debugging Evaluation & Learning
📌 After applying a fix, AI evaluates its effectiveness to refine future debugging suggestions.

🔹 AI Debugging Evaluation Metrics
Metric Purpose
Solution Reuse Rate Measures how often a past fix successfully resolves a new issue.
Fix Success Rate Tracks the percentage of debugging attempts that resolved the issue.
AI Confidence Score AI assigns a confidence level to suggested fixes.
Self-Validation Accuracy AI checks if applied fixes align with stored debugging history.
🚀 Goal: AI continuously improves debugging recall and solution accuracy.

📌 6. AI Debugging Validation & Testing
📌 Ensuring AI debugging recall & execution is accurate and reliable.

✅ Test Case 1: Debugging Recall Accuracy
📌 Test Goal: Ensure AI retrieves past debugging logs accurately.
🔹 Test Command:

ai-debug "Retrieve last 3 debugging sessions."
✅ Pass Criteria:

AI retrieves 3 relevant past debugging logs.
AI response matches previously stored error resolutions.
✅ Test Case 2: AI-Suggested Fix Accuracy
📌 Test Goal: Ensure AI suggests previously applied fixes when debugging similar issues.
🔹 Test Command:


ai-debug "Suggest a fix for a database integrity error."
✅ Pass Criteria:

AI retrieves past solutions from ChromaDB.
AI suggests a fix with a high confidence score.
✅ Test Case 3: AI Self-Debugging Execution
📌 Test Goal: AI detects, retrieves, and executes debugging solutions autonomously.
🔹 Future AI Behavior:
1️⃣ AI detects an error in api_structure.py.
2️⃣ AI queries ChromaDB for past fixes.
3️⃣ AI applies the retrieved solution autonomously.

✅ Pass Criteria:

AI executes debugging steps without human intervention.
AI verifies the fix before marking the issue as resolved.
📌 Summary
📌 This document defines the AI debugging debriefing strategy for:
✅ Structured debugging log storage & retrieval via ChromaDB
✅ AI-assisted debugging recall and solution application
✅ AI self-evaluation for debugging optimization
✅ Standardized debugging debrief format for long-term AI learning

📅 Last Updated: February 2025
🔹 Maintained by AI Recall System

## Updated Section: Integration with Blueprint Execution Logs

We can optionally track certain fields from blueprint_execution.py (e.g. 'efficiency_score', 'task_name') in our debug logs. 
Likewise, 'ai_confidence_score' (from debugging attempts) can be stored in execution logs for cross-analysis.

Example Combined Fields:
- timestamp, error/stack_trace, fix_attempted, fix_successful
- efficiency_score (or performance_score)
- potential_breakage_risk
- improvement_suggestions

## Additional Note: ChromaDB Integration
For long-term recall, we store structured debugging logs in the 'debugging_logs' collection. 
Scripts like 'query_chroma.py' provide convenience functions (list_debugging_logs, etc.) 
to verify or retrieve past debugging attempts.

## Updated Section: Strategy vs. Fix Logs
'debugging_strategy.py' adds a layer of "strategy" tracking on top of per-issue "fix" logs.
We can unify fields like error_type, fix_attempted, and success_rate to maintain consistent data
between 'debug_logs.json' and 'debugging_strategy_log.json'.
