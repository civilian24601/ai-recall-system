# 📖 AI Best Practices - AI Recall System  

## **📌 Overview**  

This document outlines the **best practices for AI-generated code, debugging recall, and workflow execution.**  

🚀 **Primary Goals:**  
✅ **Ensure AI follows structured, efficient development workflows**  
✅ **Standardize AI-generated code for readability, reusability, and maintainability**  
✅ **Optimize AI debugging recall & execution to prevent redundant problem-solving**  
✅ **Ensure AI self-improves and executes solutions efficiently with robust safety and integrity checks**  

---

## **📌 1. AI Code Generation Best Practices**  

📌 **All AI-generated code must follow structured, maintainable, and reusable formats.**  

### **🔹 AI Code Formatting Standards**

✅ **Use `snake_case` for variable and function names.**  
✅ **Ensure all functions include a docstring with clear descriptions.**  
✅ **Limit function complexity—prefer small, modular functions.**  
✅ **Avoid redundant logic—AI must retrieve stored solutions before generating new code.**  

📌 **Example AI-Generated Code (Correct Format):**

```python
def fetch_recent_debug_logs(limit: int = 5) -> list:
    """
    Retrieves the most recent debugging logs from ChromaDB.

    Args:
        limit (int): Number of logs to retrieve.

    Returns:
        list: A list of debugging log entries.
    """
    logs = query_chroma_db("SELECT * FROM debug_logs ORDER BY timestamp DESC LIMIT ?", [limit])
    return logs
✅ This ensures AI-generated code is structured, documented, and follows best practices.

📌 2. AI Debugging & Execution Best Practices
📌 AI debugging recall & execution must follow structured retrieval and validation protocols.

🔹 AI Debugging Workflow
✅ Step 1: AI retrieves debugging logs before generating new fixes.
✅ Step 2: AI prioritizes past solutions that were successfully applied.
✅ Step 3: AI ranks solutions based on confidence and context relevance.
✅ Step 4: AI suggests or applies the highest-confidence fix.

📌 Example AI Debugging Retrieval Execution:


ai-debug "Retrieve last 3 debugging sessions."
🔹 AI Response Example:


[DEBUG LOG: 2025-02-10]
Error: SQL Integrity Constraint Violation
Fix Applied: Added unique constraint in schema.
Confidence Score: 98%
✅ Prevents redundant debugging attempts and optimizes AI problem-solving efficiency.

📌 3. AI Knowledge Retrieval & ChromaDB Best Practices
📌 AI retrieval logic must prioritize accuracy, context relevance, and structured storage.

🔹 AI Query Execution Guidelines
✅ AI must first check ChromaDB for previous solutions before generating new ones.
✅ AI should rank retrieved solutions based on success rates and context similarity.
✅ AI should log every retrieval attempt and its effectiveness for self-improvement.

📌 Example AI Knowledge Query Execution:


def retrieve_past_solution(query: str) -> list:
    """
    Queries ChromaDB for stored past solutions related to the given query.

    Args:
        query (str): Description of the issue.

    Returns:
        list: Retrieved solutions ranked by confidence score.
    """
    return query_chroma_db(f"SELECT solution FROM work_logs WHERE issue LIKE '%{query}%' ORDER BY confidence DESC LIMIT 3")
✅ Ensures AI queries prioritize relevant, high-confidence solutions before proposing fixes.

## **📌 4. AI Self-Refactoring & Code Optimization Best Practices**
## **📌 AI self-refactoring should be efficient, performance-aware, and prevent unnecessary complexity.**

### **🔹 AI Code Optimization Workflow**
✅ AI must compare past optimized code snippets before modifying existing code.
✅ AI should refactor functions for efficiency without affecting core logic.
✅ AI should validate refactored code against test cases before execution.

📌 Example AI Refactoring Validation:

def validate_refactored_code(old_code: str, new_code: str) -> bool:
    """
    Validates AI-generated refactored code against best practices.

    Args:
        old_code (str): Original function.
        new_code (str): Refactored function.

    Returns:
        bool: True if changes improve performance, False otherwise.
    """
    if len(new_code) > len(old_code) * 1.2:  # Ensure AI does not overcomplicate logic
        return False

    return True
✅ Prevents AI from introducing redundant abstractions or unnecessary complexity.

📌 5. AI Execution & Oversight Best Practices
📌 AI execution workflows must follow validation steps before modifying core project files.

🔹 AI Execution Safety Guidelines
✅ AI requires human confirmation before applying critical code changes.
✅ AI logs all executed modifications for rollback and review.
✅ AI must validate the success rate of past modifications before proposing similar changes.

📌 Example AI Execution Oversight:


def ai_execution_guardrail(modification: str) -> bool:
    """
    AI execution guardrail to validate if a modification should be applied.

    Args:
        modification (str): AI-generated code modification.

    Returns:
        bool: True if modification is safe, False otherwise.
    """
    risk_score = assess_code_change_risk(modification)
    return risk_score < 10  # Only allow low-risk changes
✅ Prevents AI from making unintended modifications without validation.

📌 Summary
📌 This document provides structured AI best practices for:
✅ AI-generated code formatting, structure, and readability
✅ Debugging recall & execution workflows to optimize efficiency
✅ ChromaDB-powered AI knowledge retrieval & validation
✅ AI self-refactoring & optimization processes for continuous improvement
✅ AI execution oversight to prevent unintended modifications

📅 Last Updated: February 2025
🔹 Maintained by AI Recall System

## Updated Section: Avoid Redundant Endpoint Detection
When referencing local LLM or Flask APIs, unify logic in a shared module
so that scripts like 'user_interaction_flow.py' do not duplicate code.

## Updated Section: Logging Consistency
Currently, we have multiple scripts for logging sessions or tasks (e.g., 'log_work_session.py'
and 'work_session_logger.py'). Teams should unify naming and fields to avoid confusion.

## Updated Section: Single 'network_utils' for environment detection
Repetitive 'detect_api_url()' methods exist in scripts like 'generate_work_summary.py'.
We recommend a single shared function to maintain consistency and reduce duplication.
