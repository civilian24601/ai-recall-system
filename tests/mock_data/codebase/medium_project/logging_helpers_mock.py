"""
logging_helpers_mock.py
Simple mock logging utilities with no external dependencies.
"""

def log_info(message):
    """Prints an 'INFO' level message to console."""
    print(f"[INFO] {message}")

def log_warning(message):
    """Prints a 'WARNING' level message to console."""
    print(f"[WARNING] {message}")

def log_error(message):
    """Prints an 'ERROR' level message to console."""
    print(f"[ERROR] {message}")
