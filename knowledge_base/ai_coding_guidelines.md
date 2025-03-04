# 🤖 AI Coding Guidelines for the AI Recall System

## 📌 Overview
This document defines concise coding standards for AI-generated code, focusing on error handling, readability, and maintainability in the AI Recall System.

🚀 **Primary Goals:**
- Ensure AI writes modular, readable, maintainable code.
- Standardize function structures and error handling.
- Prevent redundant or inefficient logic.
- Guide AI debugging and self-refactoring.

---

## 📌 1. Error Handling Standards
AI must use structured `try/except` blocks for error handling, ensuring specific exceptions and clean returns.

### 🔹 Required Structure for Error Handling
- Use `try/except` with specific exception types (e.g., `ZeroDivisionError`, `KeyError`).
- Return `None` on exceptions, with no extra logic.
- Avoid generic `except:` clauses (e.g., `except:` without type).

📌 **Example for ZeroDivisionError:**

```python
def divide(a, b):
    try:
        return a / b
    except ZeroDivisionError:
        return None
📌 Example for KeyError:

def authenticate_user(user_data):
    try:
        return user_data["username"]
    except KeyError:
        return None

📌 2. AI Code Generation Best Practices
AI-generated code must be concise, readable, and maintainable.

🔹 Required Structure for Functions
Include a clear docstring describing purpose and parameters.
Use descriptive snake_case variable names.
Avoid redundant logic or loops unless necessary.
📌 Example AI-Generated Function:

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

📌 3. Debugging & Self-Refactoring
AI must follow structured debugging and refactoring workflows.

🔹 AI Debugging Workflow
Log errors in debug_logs.json (e.g., {"error": "ZeroDivisionError", "fix": "Added try/except"}).
Retrieve past solutions from ChromaDB before fixing.
Apply fixes incrementally, verifying against test cases.
🔹 AI Refactoring Workflow
Retrieve previous function versions from ChromaDB.
Analyze for performance and redundancy.
Apply changes incrementally, ensuring readability and maintainability.

📌 Example Debugging Entry:

{
    "timestamp": "2025-03-03 07:36:58",
    "error": "ZeroDivisionError",
    "fix": "Added try/except for division by zero, returning None.",
    "resolved": true
}

📌 4. ChromaDB Integration
AI retrieves stored coding patterns and debugging solutions before writing code.

🔹 Knowledge Retrieval
Query ChromaDB for past function implementations or error fixes.
Use results to modify existing solutions, avoiding redundancy.

📌 Example ChromaDB Query:

def query_ai_codebase(search_term: str) -> list:
    """
    Queries ChromaDB for AI-generated code snippets related to the search term.

    Args:
        search_term (str): The keyword to search for (e.g., "ZeroDivisionError").

    Returns:
        list: A list of matching code snippets.
    """
    results = query_chroma_db(f"SELECT snippet FROM codebase WHERE description LIKE '%{search_term}%'")
    return results

📌 Summary
AI-generated code must:

Use specific try/except for errors (e.g., ZeroDivisionError, KeyError), returning None.
Follow modular, readable structures with docstrings and snake_case.
Leverage ChromaDB for knowledge recall and debugging.
Avoid prose, explanations, or redundant logic.

📅 Last Updated: March 2025
🔹 Maintained by AI Recall System