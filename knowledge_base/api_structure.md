# 🌐 API Structure - AI Recall System

## **📌 Overview**

This document outlines the API endpoints that power the **AI Recall System**.  
The API serves as a bridge between **LM Studio, ChromaDB, and AI agents**, enabling efficient model execution and knowledge retrieval.

✅ **Backend:** Flask API  
✅ **Primary Model Execution:** LM Studio (local)  
✅ **Knowledge Retrieval:** ChromaDB  
✅ **OS Compatibility:** Supports **Windows & WSL**  

---

## **📂 API Script: `api_structure.py`**

📍 **Location:** `/mnt/f/projects/ai-recall-system/code_base/api_structure.py`

💡 **Purpose:**  

- Handles **requests to the local AI models running via LM Studio**  
- Provides endpoints for **retrieving stored knowledge from ChromaDB**  
- Supports **multi-agent workflows & debugging recall**  

---

## Updated Section: Optional API for QA or External Integrations

`api_structure.py` defines a simple Flask app exposing `/api/task`. 
- This is especially helpful for manual testing or hooking up a small UI/CLI that wants to query the local LM Studio.
- In parallel, `agent_manager.py` can also connect directly to LM Studio for behind-the-scenes automation.

### Environment Detection

We now unify environment detection (e.g., WSL vs. native Windows) via a shared utility function in `network_utils.py`. This avoids duplication and ensures consistency when referencing LM Studio’s port/IP address.


## **🔹 API URL Detection (Windows & WSL Compatibility)**

The API must handle **Windows & WSL environments** seamlessly.  
The following function **auto-detects the correct API URL**:

```python
def detect_api_url():
    """Detect the correct API URL based on whether we are in WSL or native Windows."""
    wsl_ip = "172.17.128.1"
    default_url = "http://localhost:1234/v1/chat/completions"

    try:
        with open("/proc/version", "r") as f:
            if "microsoft" in f.read().lower():
                print(f"🔹 Detected WSL! Using Windows IP: {wsl_ip}")
                return f"http://{wsl_ip}:1234/v1/chat/completions"
    except FileNotFoundError:
        pass

    print(f"🔹 Using default API URL: {default_url}")
    return default_url

✅ Ensures stable AI model interaction across OS environments.

📌 API Endpoints
1️⃣ /query/model → Execute AI Model (via LM Studio)
🔹 Description: Sends a request to LM Studio for AI-generated responses.
🔹 Method: POST
🔹 Expected Input:

{
    "model": "deepseek-coder-33b-instruct",
    "prompt": "Explain recursion in Python.",
    "temperature": 0.7
}
🔹 Example Response:

{
    "response": "Recursion is a method where the function calls itself..."
}
✅ Supports multiple models (depending on what’s loaded in LM Studio).
✅ Handles different temperature settings for response randomness.

2️⃣ /query/knowledge → Retrieve Stored Knowledge (ChromaDB)
🔹 Description: Queries ChromaDB for past work, debugging logs, or relevant project knowledge.
🔹 Method: POST
🔹 Expected Input:

{
    "query": "What debugging steps did we follow for the last API failure?"
}
🔹 Example Response:

{
    "retrieved_knowledge": "The last API failure was related to a missing API key. Debugging steps included..."
}
✅ Allows AI agents to retrieve previous work for better debugging & recall.
✅ Ensures that AI doesn’t suggest redundant fixes.

3️⃣ /query/codebase → Retrieve Code Snippets
🔹 Description: Searches the indexed project codebase for relevant functions or classes.
🔹 Method: POST
🔹 Expected Input:


{
    "query": "How do we handle API authentication?",
    "language": "python"
}
🔹 Example Response:

json
Copy
Edit
{
    "matches": [
        {
            "filename": "auth_handler.py",
            "snippet": "def authenticate_user(api_key): ..."
        }
    ]
}
✅ Allows AI to reference past implementations instead of regenerating from scratch.
✅ Helps maintain coding consistency across projects.

📌 API Deployment & Testing
📌 To start the API server:

python3 /mnt/f/projects/ai-recall-system/code_base/api_structure.py
📌 To test if the API is running (from CLI):


curl -X POST http://localhost:5000/query/model -H "Content-Type: application/json" -d '{"model":"deepseek-coder-33b-instruct", "prompt":"Explain recursion in Python."}'
📌 To test from a Python script:

import requests

url = "http://localhost:5000/query/model"
payload = {
    "model": "deepseek-coder-33b-instruct",
    "prompt": "Explain recursion in Python."
}
response = requests.post(url, json=payload)
print(response.json())
✅ Ensures the API correctly interacts with LM Studio.
✅ Can be tested easily from CLI or Python scripts.

📌 Summary
📌 This API structure ensures:
✅ Stable local AI execution via Flask API → LM Studio
✅ Windows/WSL compatibility for seamless agent workflows
✅ Direct access to knowledge recall & debugging history via ChromaDB
✅ Modular endpoints for code retrieval, knowledge recall, and model execution

📅 Last Updated: February 2025
🔹 Maintained by AI Recall System
