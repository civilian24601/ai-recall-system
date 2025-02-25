"""
auth_mock.py
Handles mock authentication logic. No external dependencies.
"""

import logging_helpers_mock

USERS_DB = {
    "alice": {"password": "1234", "roles": ["admin"]},
    "bob": {"password": "abcd", "roles": ["user"]},
}

def authenticate_user(username, password):
    """
    Checks mock USERS_DB for a valid password.
    Returns True if correct, False otherwise.
    """
    if username in USERS_DB:
        if USERS_DB[username]["password"] == password:
            logging_helpers_mock.log_info(f"User '{username}' authenticated successfully.")
            return True
    logging_helpers_mock.log_warning(f"Authentication failed for user '{username}'.")
    return False

def get_user_roles(username):
    """
    Returns a list of roles for a given user. If user not found, returns empty list.
    """
    user_data = USERS_DB.get(username)
    if user_data:
        return user_data["roles"]
    return []
