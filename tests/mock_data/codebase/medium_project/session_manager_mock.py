"""
session_manager_mock.py
Manages user sessions, referencing auth to handle roles.
"""

import auth_mock
from logging_helpers_mock import log_info, log_warning

ACTIVE_SESSIONS = {}

def start_session(username, password):
    """
    Authenticates user and creates a session if successful.
    """
    if auth_mock.authenticate_user(username, password):
        session_id = f"{username}_session"
        ACTIVE_SESSIONS[session_id] = {
            "user": username,
            "roles": auth_mock.get_user_roles(username)
        }
        log_info(f"Session started for {username} with ID={session_id}")
        return session_id
    log_warning(f"Failed to start session for {username}.")
    return None

def end_session(session_id):
    """
    Ends an active session if it exists.
    """
    if session_id in ACTIVE_SESSIONS:
        del ACTIVE_SESSIONS[session_id]
        log_info(f"Session {session_id} ended.")
    else:
        log_warning(f"No session found with ID={session_id}")
