# 🤖 AI Interaction Guidelines  

## **📌 Overview**  

This document defines the **AI Recall System’s structured approach to AI interactions**, including:  
✅ **How AI prioritizes responses for development & debugging**  
✅ **How AI recalls past interactions & solutions effectively**  
✅ **How AI transitions from human-assisted responses to AI-driven execution**  

🚀 **Current Status:** **Human-Assisted AI Responses**  
📌 **Next Step:** AI **automates recall & execution before transitioning to full autonomy.**  

---

## **📌 1. AI Response Prioritization & Structure**  

📌 **AI must follow structured response logic to ensure clarity, accuracy, and efficiency.**  

### **🔹 AI Response Rules**

✅ **Prioritize relevant solutions from past work before generating new ones**  
✅ **Retrieve structured debugging memory from ChromaDB for context-aware answers**  
✅ **Always summarize responses before expanding with additional details**  

📌 **Example AI Response Format:**  

```plaintext
🔹 **Issue Identified:** SQL Integrity Constraint Violation  
🔹 **Relevant Past Debugging Attempt:** Found fix from 2025-02-10  
🔹 **Suggested Fix:** "Add unique constraint to schema."  
🔹 **Confidence Score:** 95%  
✅ Ensures AI responses are structured, relevant, and repeatable.

📌 2. AI Memory & Recall Workflow
📌 AI relies on structured recall via ChromaDB before suggesting solutions.

🔹 How AI Retrieves Past Work
1️⃣ AI queries ChromaDB for stored solutions & debugging attempts.
2️⃣ AI compares retrieved solutions with the current problem context.
3️⃣ AI prioritizes the most relevant past fix before generating new ones.

📌 Example AI Query Execution:

def ai_retrieve_past_work(query: str) -> list:
    """
    Searches ChromaDB for past work related to the given query.

    Args:
        query (str): Description of the issue or task.

    Returns:
        list: Matching past work logs.
    """
    return query_chroma_db(f"SELECT solution FROM work_logs WHERE issue LIKE '%{query}%'")
✅ Prevents redundant work & ensures AI recall is efficient.

📌 3. AI Debugging & Execution Protocols
📌 AI debugging recall & execution follows structured protocols to avoid unnecessary troubleshooting loops.

🔹 AI Debugging & Execution Workflow
✅ Step 1: AI detects an issue and logs it in debug_logs.json.
✅ Step 2: AI retrieves past debugging solutions via ChromaDB.
✅ Step 3: AI ranks retrieved solutions by confidence & relevance.
✅ Step 4: AI applies the fix autonomously (if in self-debugging mode).
✅ Step 5: AI validates the fix & updates debugging history.

📌 Example Debugging Recall Execution:

ai-debug "Retrieve last 3 debugging sessions."
🔹 AI Response Example:


[DEBUG LOG: 2025-02-10]
Error: SQL Integrity Constraint Violation
Fix Applied: Added unique constraint in schema.
Confidence Score: 98%
✅ Ensures AI debugging recall is structured and reliable.

📌 4. AI Interaction Scenarios
📌 AI follows structured interaction patterns to handle different workflows.

Scenario AI Behavior
Developer Requests Past Work 
AI retrieves & summarizes relevant solutions.
AI Detects an Error 
AI self-queries ChromaDB before generating a new fix.
AI Suggests a Fix 
AI ranks confidence levels & proposes the highest-scoring fix.
AI Writes New Code 
AI checks past implementations before generating new functions.
✅ Ensures AI interactions remain predictable and consistent.

📌 5. AI Multi-Agent Collaboration Principles
📌 AI follows structured collaboration principles when transitioning to multi-agent workflows.

🔹 AI Multi-Agent Expansion Plan
Agent Primary Role
Engineer Agent Writes, refactors, and optimizes AI-generated code.
QA Agent Tests AI modifications & ensures debugging recall accuracy.
Debug Agent Detects errors, retrieves past solutions, and applies fixes.
Oversight Agent Monitors AI behavior & prevents execution failures.
✅ Ensures AI agents work together effectively as the system evolves.

📌 6. Future AI Self-Improvement Strategy
📌 AI continuously refines its responses by evaluating past recall accuracy.

🔹 AI Self-Optimization Workflow
✅ AI logs response effectiveness & retrieval accuracy
✅ AI updates its weighting system based on past recall success
✅ AI ranks debugging recall effectiveness to improve future solutions

📌 Example AI Self-Improvement Log Entry:

{
    "timestamp": "2025-02-11 10:05:42",
    "query": "Fix last API failure",
    "retrieved_solution_accuracy": 92%,
    "new_solution_applied": true,
    "improvement_score": 87%
}
✅ Ensures AI recall & debugging workflows continually improve over time.

📌 Summary
📌 This document defines structured AI interaction principles for:
✅ AI response prioritization & structured memory recall
✅ AI debugging recall & autonomous fix execution
✅ Multi-agent collaboration & self-improvement strategies
✅ AI self-evaluation for continuously improving recall accuracy

📅 Last Updated: February 2025
🔹 Maintained by AI Recall System

## Updated Section: Dual Approach (Direct vs. Flask)

As of March 2025, the system supports two methods for AI interactions:

1. **Direct-to-LM-Studio** (via HTTP POST to localhost or WSL IP) 
   - Used primarily by scripts like `agent_manager.py`
   - Provides internal automation and agent-based logic

2. **Flask-based Endpoint** (via `/api/task`)
   - Implemented in `api_structure.py`
   - Useful for manual testing or exposing a stable interface to external tools
   - Calls the same local LM Studio but behind a simple REST layer

Both methods rely on the shared `network_utils.py` for environment detection, ensuring consistent usage across WSL or native Windows.

## Updated Section: Multiple Refinements & Fallback Strategies

For catastrophic or repeated sub-threshold failures:
1. The system triggers a blueprint revision (blueprint_execution.py).
2. Future expansions can automatically chain multiple agent roles (engineer, debug, oversight) to refine or correct the blueprint 
   before final acceptance, removing manual 'Pending Review' steps.
3. If X attempts fail, fallback to a simplified or known stable fix.

## Updated Section: Single-Step Knowledge + LLM Query
core_architecture.py's AIManager class first attempts a direct textual match in the knowledge base, then calls the LLM if no relevant snippet is found. Future expansions could:
- Retry with multiple prompts if partial matches occur
- Log all misses in debugging logs for historical reference

## Updated Section: CLI Flow Example
'user_interaction_flow.py' exemplifies a user → knowledge base → fallback LLM approach.
Future expansions may allow multiple clarifications or a multi-agent escalation if
the user is unsatisfied with the first result.

# 🧑‍💻 User Interaction Flow - AI Recall System

## **📌 Overview**

**This document outlines how the AI Recall System interacts with both human developers and autonomous AI workflows**.  

🚀 **Current State:**  

- **Developers interact via CLI and API requests**  
- **AI assists with code retrieval, debugging recall, and structured work memory**  

🌍 **Future Goal:**  

- **AI self-queries past solutions automatically**  
- **AI autonomously retrieves debugging logs & executes self-fixes**  
- **Human oversight is reserved for validation & creativity, not manual recall**  

✅ **Access Points for Interaction:**  

- **CLI Commands → Manual retrieval of past knowledge & debugging logs**  
- **AI-to-AI Querying (Future) → AI autonomously queries & applies past knowledge**  

---

## **📌 Current Human-to-AI Workflows (Manual Interactions)**

📌 **Today, developers interact with the system using:**  

| **Method** | **Description** |
|------------|------------------------------------------------|
| **CLI Commands** | Manually retrieve knowledge & debug history. |
| **Continue.dev AI Chat** | Ask AI for coding help inside VS Code.(phasing out) |
| **API Endpoints** | Query stored knowledge for external integrations. |

📌 **Example CLI Usage**

```bash
ai-recall "How did we solve API rate limiting?"
✅ Retrieves past solutions from ChromaDB

📌 Future AI-to-AI Workflow (Autonomous Queries)
📌 As the system evolves, AI will automatically handle recall & debugging.

Process Future AI Behavior
Self-Querying Past Work AI autonomously checks past debugging logs before proposing fixes.
Code Improvement Suggestions AI proactively recommends optimizations based on stored best practices.
Self-Triage of Issues AI detects errors and retrieves past solutions before executing a fix.
📌 Example AI Behavior (Future) 🚀 Instead of the developer typing:


ai-debug "What was the last database error?"
✅ The AI will autonomously run the same query, fetch results, and apply a fix without human intervention.

📌 Continue.dev - AI-Assisted Coding in VS Code
📌 Currently, developers manually query AI for suggestions.
📌 Eventually, the AI will use Continue.dev APIs to self-optimize codebases.

Feature Current Use Future AI Behavior
@codebase Manually retrieve code snippets AI auto-searches relevant project files
@docs Pull documentation manually AI references docs before executing fixes
AI Chat Direct human interaction AI-to-AI querying for workflow automation
📌 Future AI Workflow Example 1️⃣ AI encounters an error in api_structure.py
2️⃣ AI queries debugging logs autonomously
3️⃣ AI retrieves and applies the previous fix
4️⃣ AI validates that the issue is resolved before deployment

✅ Reduces human intervention in debugging cycles.

📌 API-Assisted AI Interaction
📌 Currently, API endpoints allow external tools to interact with the AI Recall System.
📌 In the future, AI will self-query these endpoints automatically.

🔹 Query Stored Knowledge (/query/knowledge)
Method: POST
Example Request:

{
    "query": "What debugging steps were used for the last API failure?"
}
Example Response:

json
Copy
Edit
{
    "retrieved_knowledge": "The last API failure was related to a missing API key. Debugging steps included..."
}
✅ AI will eventually call this endpoint autonomously during error handling.

📌 Summary
📌 This document ensures developers can efficiently interact with AI for:
✅ Current Manual Workflows (CLI, Continue.dev, API queries)
✅ Future AI-to-AI Workflows (Autonomous debugging, self-querying memory)
✅ Seamless evolution from human-AI interaction to full AI-driven execution


