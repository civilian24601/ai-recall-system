"""
api_routes_mock.py
Pretends to define some API routes for a local server.
No real web framework here, just placeholders.
"""

import db_manager_mock
from logging_helpers_mock import log_info, log_warning

def handle_get_user_data(user):
    """
    Mock GET user data route.
    Connects to DB and runs a 'query' to fetch user data (fake).
    """
    if not db_manager_mock.connect_to_database():
        log_warning("DB connect failed in handle_get_user_data!")
        return {}
    results = db_manager_mock.run_query(f"SELECT * FROM users WHERE name='{user}'")
    db_manager_mock.disconnect_database()
    log_info(f"Fetched user data for {user}: {results}")
    return {"user": user, "data": results}

def handle_post_update_user(user, new_data):
    """
    Mock POST to update user data, returning success or fail.
    """
    if db_manager_mock.connect_to_database():
        # pretend we do an UPDATE
        db_manager_mock.run_query(f"UPDATE users SET info='{new_data}' WHERE name='{user}'")
        db_manager_mock.disconnect_database()
        return True
    return False
