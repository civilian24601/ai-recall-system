import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

def connect_to_database():
    """Attempts to connect to the database but times out."""
    try:
        engine = create_engine('your-db-uri', connect_args={"connect_timeout": 5})  # ❌ Too low timeout
        connection = engine.connect()
        return connection
    except OperationalError as e:
        print(f"Database Connection Failed: {e}")
        return None
