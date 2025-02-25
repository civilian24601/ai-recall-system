"""
db_handler_mock.py
A minimal mock for database connection logic, no real DB needed.
"""

def connect_to_db():
    """
    Mock DB connection. Returns True to simulate success.
    """
    print("Mock DB connected successfully.")
    return True

def run_query(sql):
    """
    Pretend to run an SQL query, returns a fake result set.
    """
    print(f"Running mock query: {sql}")
    return ["row1", "row2"]
