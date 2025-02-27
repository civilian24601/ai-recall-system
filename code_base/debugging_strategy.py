import json
import datetime
import hashlib
import os
import logging

import chromadb  # For storing snippet strategies in Chroma

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DebuggingStrategy:
    """Manages AI debugging strategies and tracks effectiveness."""

    def __init__(self, test_mode=False):
        # [UPDATED] Switch file paths if test_mode
        if test_mode:
            self.debug_logs_file = "tests/test_logs/debug_logs_test.json"
            self.strategy_log_file = "tests/test_logs/debugging_strategy_log_test.json"
        else:
            self.debug_logs_file = "../logs/debug_logs.json"
            self.strategy_log_file = "../logs/debugging_strategy_log.json"

        # Connect to Chroma for snippet success rates
        self.chroma_client = chromadb.PersistentClient(path="/mnt/f/projects/ai-recall-system/chroma_db/")
        
        # [SAME AS BEFORE] 
        self.strategies_collection_name = (
            "debugging_strategies_test" if test_mode else "debugging_strategies"
        )
        self.strategies_collection = self.chroma_client.get_or_create_collection(
            name=self.strategies_collection_name
        )

    def load_strategy_logs(self):
        """Loads past debugging strategies from local JSON."""
        try:
            with open(self.strategy_log_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"Failed to load strategy logs: {e}")
            return []  # Return empty if file missing or corrupted

    def save_strategy_logs(self, strategies):
        """Saves updated debugging strategies to local JSON."""
        try:
            with open(self.strategy_log_file, "w") as f:
                json.dump(strategies, f, indent=4)
        except Exception as e:
            logging.error(f"Failed to save strategy logs: {e}")

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
        try:
            doc_id = self.build_strategy_doc_id(error_type, snippet)
            doc_json = json.dumps(strategy_record)

            # Minimal metadata for searching
            metadata = {
                "error_type": error_type,
                "snippet_hash": doc_id,
                "attempts": strategy_record.get("attempts", 0),
                "success_rate": strategy_record.get("success_rate", 0.0),
            }

            existing_docs = self.strategies_collection.get(ids=[doc_id])
            if existing_docs and "documents" in existing_docs and existing_docs["documents"]:
                logging.info(f"Strategy doc ID '{doc_id}' already exists. Updating existing entry.")
                self.strategies_collection.update(
                    ids=[doc_id],
                    documents=[doc_json],
                    metadatas=[metadata]
                )
            else:
                self.strategies_collection.add(
                    ids=[doc_id],
                    documents=[doc_json],
                    metadatas=[metadata]
                )
            logging.info(f"Synced strategy doc ID '{doc_id}' to Chroma collection '{self.strategies_collection_name}'.")
        except Exception as e:
            logging.error(f"Failed to sync strategy with Chroma: {e}")

    def get_debugging_strategy(self, error_type):
        """
        Returns the snippet with highest success_rate for error_type,
        or a default fallback if none found in local JSON. 
        (No direct Chroma query for single best snippet yet.)
        """
        try:
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
        except Exception as e:
            logging.error(f"Failed to get debugging strategy: {e}")
            return "Standard debugging: AI will analyze logs, suggest fixes, and request verification."

    def update_strategy(self, error_type, snippet, success):
        """
        Updates or creates a debugging strategy record based on
        the new fix attempt's success. Also upserts into Chroma.
        """
        try:
            strategies = self.load_strategy_logs()

            # Normalize snippet to reduce duplicates
            norm_snippet = self.normalize_snippet(snippet)

            for entry in strategies:
                # Match both error_type and the EXACT snippet
                if entry["error_type"] == error_type and entry["strategy"] == norm_snippet:
                    entry["attempts"] += 1
                    if success:
                        entry["successful_fixes"] += 1
                    entry["success_rate"] = entry["successful_fixes"] / entry["attempts"]

                    self.save_strategy_logs(strategies)
                    self.sync_strategy_with_chroma(error_type, norm_snippet, entry)
                    return

            # If no matching entry, create a new one
            new_record = {
                "error_type": error_type,
                "strategy": norm_snippet,
                "attempts": 1,
                "successful_fixes": 1 if success else 0,
                "success_rate": 1.0 if success else 0.0
            }
            strategies.append(new_record)
            self.save_strategy_logs(strategies)

            # Upsert to Chroma
            self.sync_strategy_with_chroma(error_type, norm_snippet, new_record)
        except Exception as e:
            logging.error(f"Failed to update strategy: {e}")

    def analyze_previous_fixes(self):
        """
        Reads debug_logs.json, updates snippet success records for each fix attempt.
        Normalizes the snippet to reduce duplicates, then upserts to local + Chroma.
        """
        try:
            with open(self.debug_logs_file, "r") as f:
                debug_logs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"Failed to load debug logs: {e}")
            return

        for entry in debug_logs:
            if "error" in entry and "fix_attempted" in entry:
                logging.info(f"Processing error log: {entry['error']}")
                success_flag = (entry.get("fix_successful") is True)
                norm_snippet = self.normalize_snippet(entry["fix_attempted"])
                self.update_strategy(entry["error"], norm_snippet, success=success_flag)

# 🚀 Example Usage
if __name__ == "__main__":
    debugger = DebuggingStrategy(test_mode=False)
    debugger.analyze_previous_fixes()
    # Optionally retrieve best known snippet for some error
    best_snippet = debugger.get_debugging_strategy("ZeroDivisionError: division by zero")
    print(f"Best known snippet for ZeroDivisionError: {best_snippet}")
