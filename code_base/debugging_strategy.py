import json
import datetime
import hashlib

import chromadb  # <-- NEW

class DebuggingStrategy:
    """Manages AI debugging strategies and tracks effectiveness."""

    def __init__(self, test_mode=False):
        self.strategy_log_file = "../logs/debugging_strategy_log.json"
        self.debug_logs_file = "../logs/debug_logs.json"

        # Connect to Chroma for snippet success rates
        self.chroma_client = chromadb.PersistentClient(path="/mnt/f/projects/ai-recall-system/chroma_db/")
        self.strategies_collection_name = "debugging_strategies_test" if test_mode else "debugging_strategies"
        self.strategies_collection = self.chroma_client.get_or_create_collection(name=self.strategies_collection_name)

    def load_strategy_logs(self):
        """Loads past debugging strategies from local JSON."""
        try:
            with open(self.strategy_log_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []  # Return empty if file missing or corrupted

    def save_strategy_logs(self, strategies):
        """Saves updated debugging strategies to local JSON."""
        with open(self.strategy_log_file, "w") as f:
            json.dump(strategies, f, indent=4)

    def normalize_snippet(self, snippet):
        """
        Removes triple backticks, 'python', extra blank lines, and trailing whitespace
        to deduplicate near-identical fix attempts.
        """
        if not snippet:
            return ""
        snippet = snippet.replace("```", "")
        snippet = snippet.replace("python", "")
        lines = [line.strip() for line in snippet.split("\n") if line.strip()]
        return "\n".join(lines)

    def build_strategy_doc_id(self, error_type, snippet):
        """
        Creates a unique ID for each error_type + snippet combo,
        e.g. via hashing to keep it short.
        """
        unique_str = f"{error_type}::{snippet}"
        doc_id = hashlib.sha256(unique_str.encode("utf-8")).hexdigest()[:16]
        return doc_id

    def sync_strategy_with_chroma(self, error_type, snippet, strategy_record):
        """
        Upserts the snippet strategy record into the 'debugging_strategies' or
        'debugging_strategies_test' collection.
        """
        doc_id = self.build_strategy_doc_id(error_type, snippet)
        doc_json = json.dumps(strategy_record)

        # Minimal metadata for searching
        metadata = {
            "error_type": error_type,
            "snippet_hash": doc_id,
            "attempts": strategy_record.get("attempts", 0),
            "success_rate": strategy_record.get("success_rate", 0.0),
        }

        self.strategies_collection.add(
            ids=[doc_id],
            documents=[doc_json],
            metadatas=[metadata]
        )
        print(f"🔄 Synced strategy doc ID='{doc_id}' to Chroma collection '{self.strategies_collection_name}'.")

    def get_debugging_strategy(self, error_type):
        """
        Returns the snippet with highest success_rate for error_type,
        or a default fallback if none found in local JSON. (No Chroma query yet.)
        """
        strategies = self.load_strategy_logs()
        matching_strategies = [s for s in strategies if s["error_type"] == error_type]

        if matching_strategies:
            best_strategy = sorted(
                matching_strategies,
                key=lambda x: x["success_rate"],
                reverse=True
            )[0]
            return best_strategy["strategy"]

        # Default fallback
        return "Standard debugging: AI will analyze logs, suggest fixes, and request verification."

    def update_strategy(self, error_type, snippet, success):
        """
        Updates or creates a debugging strategy record based on
        the new fix attempt's success. Also upserts into Chroma.
        """
        strategies = self.load_strategy_logs()

        for entry in strategies:
            # Match both error_type and the exact snippet
            if entry["error_type"] == error_type and entry["strategy"] == snippet:
                entry["attempts"] += 1
                if success:
                    entry["successful_fixes"] += 1
                entry["success_rate"] = entry["successful_fixes"] / entry["attempts"]

                self.save_strategy_logs(strategies)
                # Upsert to Chroma
                self.sync_strategy_with_chroma(error_type, snippet, entry)
                return

        # If no matching entry, create a new one
        new_record = {
            "error_type": error_type,
            "strategy": snippet,
            "attempts": 1,
            "successful_fixes": 1 if success else 0,
            "success_rate": 1.0 if success else 0.0
        }
        strategies.append(new_record)
        self.save_strategy_logs(strategies)

        # Upsert to Chroma
        self.sync_strategy_with_chroma(error_type, snippet, new_record)

    def analyze_previous_fixes(self):
        """
        Reads debug_logs.json, updates snippet success records for each fix attempt.
        Normalizes the snippet to reduce duplicates, then upserts to local + Chroma.
        """
        try:
            with open(self.debug_logs_file, "r") as f:
                debug_logs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return

        for entry in debug_logs:
            if "error" in entry and "fix_attempted" in entry:
                print(f"🔍 Processing error log: {entry['error']}")
                success_flag = (entry.get("fix_successful") is True)
                norm_snippet = self.normalize_snippet(entry["fix_attempted"])
                self.update_strategy(entry["error"], norm_snippet, success=success_flag)

# 🚀 Example Usage
if __name__ == "__main__":
    # For production, test_mode=False
    debugger = DebuggingStrategy(test_mode=False)
    debugger.analyze_previous_fixes()

    # Example: get a strategy
    strategy = debugger.get_debugging_strategy("ZeroDivisionError: division by zero")
    print(f"Recommended Debugging Strategy: {strategy}")
# ✅ Example Output
# 
# 🔍 Processing error log: ZeroDivisionError: division by zero
# 🔄 Synced strategy doc ID='c0f2d1f7e7c2d4a0' to Chroma collection 'debugging_strategies'.
# Recommended Debugging Strategy: Standard debugging: AI will analyze logs, suggest fixes, and request verification.
# 
# 🔍 Processing error log: NameError: name 'conn' is not defined
# 🔄 Synced strategy doc ID='b4f4b7d8c3e1e2d8' to Chroma collection 'debugging_strategies'.
# Recommended Debugging Strategy: Standard debugging: AI will analyze logs, suggest fixes, and request verification.
# 
# 🔍 Processing error log: AttributeError: 'NoneType' object has no attribute 'execute'
# 🔄 Synced strategy doc ID='a3b2a1d4f8b7c2e1' to Chroma collection 'debugging_strategies'.
# Recommended Debugging Strategy: Standard debugging: AI will analyze logs, suggest fixes, and request verification.
# 
# 🔍 Processing error log: ZeroDivisionError: division by zero
# 🔄 Synced strategy doc ID='c0f2d1f7e7c2d4a0' to Chroma collection 'debugging_strategies'.
# Recommended Debugging Strategy: Standard debugging: AI will analyze logs, suggest fixes, and request verification.
# 
# 🔍 Processing error log: NameError: name 'conn' is not defined
# 🔄 Synced strategy doc ID='b4f4b7d8c3e1e2d8' to Chroma collection 'debugging_strategies'.
# Recommended Debugging Strategy: Standard debugging: AI will analyze logs, suggest fixes, and request verification.
# 
# 🔍 Processing error log: AttributeError: 'NoneType' object has no attribute 'execute'
# 🔄 Synced strategy doc ID='a3b2a1d4f8b7c2e1' to Chroma collection 'debugging_strategies'.
# Recommended Debugging Strategy: Standard debugging: AI will analyze logs, suggest fixes, and request verification.
# 
# 🔍 Processing error log: ZeroDivisionError: division by zero
# 🔄 Synced strategy doc ID='c0f2d1f