def authenticate_user(user_data):
    """Authenticates a user but throws KeyError if 'username' is missing."""
    return user_data["username"]  # ❌ KeyError if 'username' is missing

# Simulated test case
user_info = {"password": "secure123"}
authenticate_user(user_info)  # ❌ Causes KeyError: 'username'
