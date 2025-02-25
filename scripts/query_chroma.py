import chromadb
import json

# Initialize ChromaDB client
chroma_client = chromadb.PersistentClient(path="/mnt/f/projects/ai-recall-system/chroma_db/")
execution_logs = chroma_client.get_or_create_collection(name="execution_logs")
blueprint_versions = chroma_client.get_or_create_collection(name="blueprint_versions")
revision_proposals = chroma_client.get_or_create_collection(name="blueprint_revisions")
work_sessions = chroma_client.get_or_create_collection(name="work_sessions")
debugging_logs = chroma_client.get_or_create_collection(name="debugging_logs")

def list_execution_logs(limit=100):
    """Retrieve and print a summary of stored execution logs."""
    results = execution_logs.get(limit=limit)

    if not results or "documents" not in results or not results["documents"]:
        print("⚠ No execution logs found in ChromaDB.")
        return

    print("\n📌 Stored Execution Logs in ChromaDB (summary):")
    for doc in results["documents"]:
        log_data = json.loads(doc)
        task_name = log_data.get("task_name", "UNKNOWN")
        exc_id = log_data.get("execution_trace_id", "NO_ID")
        success = log_data.get("success")
        efficiency = log_data.get("efficiency_score")
        short_str = (f" - [ExecID: {exc_id}] Task={task_name}, success={success}, "
                     f"eff={efficiency}")
        print(short_str)

def list_revision_proposals(limit=50):
    """Retrieve and print a summary of stored Blueprint Revision Proposals."""
    results = revision_proposals.get(limit=limit)

    if not results or "documents" not in results or not results["documents"]:
        print("⚠ No blueprint revision proposals found in ChromaDB.")
        return

    print("\n📌 Stored Blueprint Revision Proposals (summary):")
    for doc in results["documents"]:
        rev_data = json.loads(doc)
        rev_id = rev_data.get("revision_id")
        bpid = rev_data.get("blueprint_id")
        status = rev_data.get("status")
        short_str = (f" - [RevID: {rev_id}] For blueprint={bpid}, status={status}")
        print(short_str)

def list_work_sessions(limit=50):
    """Retrieve and print a summary of stored work session logs."""
    results = work_sessions.get(limit=limit)

    if not results or "documents" not in results or not results["documents"]:
        print("⚠ No work sessions found in ChromaDB.")
        return

    print("\n📌 Stored Work Session Logs (summary):")
    for doc in results["documents"]:
        sess_data = json.loads(doc)
        sid = sess_data.get("id") or sess_data.get("timestamp")
        outcome = sess_data.get("outcome", "N/A")
        short_str = f" - [SessionID: {sid}] outcome={outcome}"
        print(short_str)

def list_debugging_logs(limit=50):
    """Retrieve and print a summary of stored debugging logs."""
    results = debugging_logs.get(limit=limit)

    if not results or "documents" not in results or not results["documents"]:
        print("⚠ No debugging logs found in ChromaDB.")
        return

    print("\n📌 Stored Debugging Logs (summary):")
    for doc in results["documents"]:
        dbg_data = json.loads(doc)
        dbgid = dbg_data.get("id") or dbg_data.get("timestamp")
        error_msg = dbg_data.get("error_message", "N/A")
        short_str = f" - [DebugID: {dbgid}] error={error_msg}"
        print(short_str)

def get_work_sessions(limit=5):
    """Retrieve the last N AI work sessions from ChromaDB (raw)."""
    results = work_sessions.get(limit=limit)
    return [json.loads(doc) for doc in results["documents"]] if results and "documents" in results else []

def get_past_execution_attempts(task_name, limit=10):
    """
    Retrieve past execution logs for a given task (metadata filter).
    We'll return them as raw dicts for possible further usage,
    but we won't print them fully here.
    """
    results = execution_logs.get(where={"task_name": task_name}, limit=limit)

    if not results or "documents" not in results:
        return []

    return [json.loads(doc) for doc in results["documents"]]

if __name__ == "__main__":
    print("\n🔹 Blueprints:")

    # Execution logs
    list_execution_logs()

    # Revision proposals
    list_revision_proposals()

    # Work sessions
    list_work_sessions()

    # Debug logs
    list_debugging_logs()

    # Example: retrieve raw logs for a certain task
    print("\n🔹 Work Session Logs from ChromaDB:", get_work_sessions())
    print(f"\n🔍 Past Execution Attempts for 'Refactor query logic in query_chroma.py':")
    matching_runs = get_past_execution_attempts(task_name="Refactor query logic in query_chroma.py")
    print(matching_runs)  # if you want a raw print
