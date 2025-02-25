# 🤖 AI Coding Guidelines  

## **📌 Overview**  

This document defines the **coding standards & best practices** for AI-generated code in the AI Recall System.  

🚀 **Primary Goals:**  
✅ **Ensure AI writes modular, readable, and maintainable code**  
✅ **Standardize AI-generated function structures and documentation**  
✅ **Prevent AI from introducing redundant or inefficient logic**  
✅ **Guide AI-assisted debugging and code self-refactoring processes**  

---

## **📌 1. AI Code Generation Best Practices**  

📌 **AI-generated code must follow a structured format to ensure readability and maintainability.**  

### **🔹 Required Structure for AI-Generated Functions**

✅ **Every function must have a clear docstring describing its purpose and parameters.**  
✅ **AI must include inline comments for complex logic.**  
✅ **Variable names should be descriptive and follow `snake_case`.**  

📌 **Example AI-Generated Function:**

```python
def fetch_latest_debug_logs(limit: int = 5) -> list:
    """
    Retrieves the latest debugging logs from ChromaDB.

    Args:
        limit (int): Number of logs to retrieve.

    Returns:
        list: A list of debugging log entries.
    """
    logs = query_chroma_db("SELECT * FROM debug_logs ORDER BY timestamp DESC LIMIT ?", [limit])
    return logs
✅ This ensures AI-generated code is readable, well-documented, and reusable.

📌 2. AI Self-Refactoring Guidelines
📌 AI must follow strict validation steps when refactoring code to prevent unintended changes.

🔹 AI Refactoring Workflow
1️⃣ Retrieve previous versions of the function from ChromaDB.
2️⃣ Analyze performance & redundancy before refactoring.
3️⃣ Apply changes incrementally and verify against test cases.
4️⃣ Log modifications for future AI recall.

📌 Example AI Refactoring Validation:

python
Copy
Edit
def validate_refactored_code(old_code: str, new_code: str) -> bool:
    """
    Compares old and new code to ensure refactoring improved performance and readability.

    Args:
        old_code (str): Original function code.
        new_code (str): Refactored function code.

    Returns:
        bool: True if changes are valid, False otherwise.
    """
    if len(new_code) < len(old_code) * 0.9:  # Ensure refactor does not introduce unnecessary complexity
        return False

    return True  # If refactor passes validation, return True
✅ Prevents AI from making unnecessary modifications that worsen code quality.

📌 3. Debugging & Error Handling Standards
📌 AI must follow a structured debugging approach when identifying & fixing errors.

🔹 AI Debugging Workflow
✅ Step 1: AI logs detected errors in debug_logs.json.
✅ Step 2: AI retrieves past debugging solutions before suggesting a fix.
✅ Step 3: AI applies the fix (if in self-debugging mode) or recommends the change to the user.

📌 Example AI Debugging Entry

json
Copy
Edit
{
    "timestamp": "2025-02-10 14:23:11",
    "error": "SQL Integrity Constraint Violation",
    "fix_applied": "Added unique constraint to the schema.",
    "developer_reviewed": true
}
✅ Ensures AI debugging recall is structured and reliable.

📌 4. AI Code Review & Validation Process
📌 All AI-generated code must be validated before execution.

🔹 AI Code Review Checklist
✔ Function structure follows defined best practices.
✔ Variables and function names are descriptive and consistent.
✔ No redundant or unnecessary loops introduced.
✔ Changes do not impact system performance negatively.

📌 Example AI Code Review Process:

python
Copy
Edit
def review_ai_generated_code(code_snippet: str) -> bool:
    """
    Reviews AI-generated code to ensure it follows best practices.

    Args:
        code_snippet (str): AI-generated Python function.

    Returns:
        bool: True if the code is valid, False otherwise.
    """
    if "def " not in code_snippet or '"""' not in code_snippet:
        return False  # Ensure function has a docstring

    if "for " in code_snippet and "while " in code_snippet:
        return False  # Ensure AI does not introduce unnecessary loops

    return True
✅ Prevents AI from introducing low-quality or redundant code.

📌 5. ChromaDB Integration for AI Code Recall
📌 AI retrieves stored coding patterns & debugging solutions before writing new code.

🔹 AI Knowledge Retrieval Workflow
1️⃣ Query ChromaDB for past function implementations.
2️⃣ Compare retrieved results against the current task.
3️⃣ Modify existing solutions before generating entirely new code.

📌 Example ChromaDB Query for AI Code Retrieval

python
Copy
Edit
def query_ai_codebase(search_term: str) -> list:
    """
    Queries ChromaDB for AI-generated code snippets related to the search term.

    Args:
        search_term (str): The keyword to search for.

    Returns:
        list: A list of matching code snippets.
    """
    results = query_chroma_db(f"SELECT snippet FROM codebase WHERE description LIKE '%{search_term}%'")
    return results
✅ Ensures AI reuses stored knowledge instead of generating redundant solutions.

📌 6. AI Multi-Agent Collaboration for Code Execution
📌 Future AI development will involve multiple agents working together on self-improving code.

Agent Role
Engineer Agent Writes & refactors AI-generated code.
QA Agent Tests AI modifications before execution.
Oversight Agent Prevents AI from making unauthorized code changes.
🚀 Goal: AI agents coordinate to generate, review, and optimize code collaboratively.

📌 Summary
📌 This document ensures AI-generated code follows structured guidelines for:
✅ Readability, maintainability, and best practices
✅ AI self-refactoring & validation workflows
✅ Debugging recall & structured AI troubleshooting
✅ ChromaDB-powered AI knowledge retrieval
✅ Multi-agent AI collaboration for future code execution

📅 Last Updated: February 2025
🔹 Maintained by AI Recall System
