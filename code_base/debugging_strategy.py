import json
import datetime

class DebuggingStrategy:
    """Manages AI debugging strategies and tracks effectiveness."""

    def __init__(self):
        self.strategy_log_file = "../logs/debugging_strategy_log.json"
        self.debug_logs_file = "../logs/debug_logs.json"

    def load_strategy_logs(self):
        """Loads past debugging strategies from log file."""
        try:
            with open(self.strategy_log_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []  # Return empty if file is missing or corrupted

    def save_strategy_logs(self, strategies):
        """Saves updated debugging strategies to log file."""
        with open(self.strategy_log_file, "w") as f:
            json.dump(strategies, f, indent=4)

    def normalize_snippet(self, snippet):
        """
        Removes triple backticks, language fences (like 'python'),
        extra blank lines, and trailing whitespace.
        This helps deduplicate near-identical fix attempts.
        """
        if not snippet:
            return ""

        # Remove triple backticks
        snippet = snippet.replace("```", "")
        # Remove 'python' if used as a fence or marker
        snippet = snippet.replace("python", "")

        # Split by lines, strip each, remove empty lines
        lines = [line.strip() for line in snippet.split("\n") if line.strip()]
        # Rejoin into a normalized multi-line string
        normalized = "\n".join(lines)

        return normalized

    def get_debugging_strategy(self, error_type):
        """
        Returns a debugging strategy with the highest success rate
        for the given error_type, or a default strategy if none found.
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

    def update_strategy(self, error_type, strategy, success):
        """
        Updates (or creates) a debugging strategy record based on the
        new fix attempt's success.
        """
        strategies = self.load_strategy_logs()

        for entry in strategies:
            # Match both error_type and the exact snippet
            if entry["error_type"] == error_type and entry["strategy"] == strategy:
                # Update attempts
                entry["attempts"] += 1
                if success:
                    entry["successful_fixes"] += 1
                entry["success_rate"] = entry["successful_fixes"] / entry["attempts"]
                self.save_strategy_logs(strategies)
                return

        # If no matching entry, create a new one
        strategies.append({
            "error_type": error_type,
            "strategy": strategy,
            "attempts": 1,
            "successful_fixes": 1 if success else 0,
            "success_rate": 1.0 if success else 0.0
        })

        self.save_strategy_logs(strategies)

    def analyze_previous_fixes(self):
        """
        Reads debug_logs.json, updates strategy records based on
        each logged fix. Uses the real 'fix_successful' field to set success rates.
        Normalizes the snippet to reduce duplicates.
        """
        try:
            with open(self.debug_logs_file, "r") as f:
                debug_logs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return

        for entry in debug_logs:
            # Only process logs that contain an "error" and "fix_attempted"
            if "error" in entry and "fix_attempted" in entry:
                print(f"🔍 Processing error log: {entry['error']}")
                success_flag = (entry.get("fix_successful") is True)
                norm_snippet = self.normalize_snippet(entry["fix_attempted"])
                self.update_strategy(
                    entry["error"],
                    norm_snippet,
                    success=success_flag
                )

# 🚀 Example Usage
if __name__ == "__main__":
    debugger = DebuggingStrategy()
    debugger.analyze_previous_fixes()

    # Example: Get a debugging strategy for a known error
    strategy = debugger.get_debugging_strategy("ZeroDivisionError: division by zero")
    print(f"Recommended Debugging Strategy: {strategy}")
