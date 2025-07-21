import pytest
import os
from dotenv import load_dotenv
import psycopg2

# Load environment variables for the test environment
load_dotenv()

@pytest.fixture(scope="module")
def db_connection():
    """
    A pytest fixture that creates a database connection for a test module.
    It automatically handles closing the connection after all tests in the module are done.
    """
    conn = None
    try:
        conn = psycopg2.connect(
            host="db",
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "vet_epigeoai_db"),
            user=os.getenv("DB_USER", "vet_user"),
            password=os.getenv("DB_PASSWORD", "strongpassword")
        )
        print("\n[Test DB] Connection established.")
        yield conn
    finally:
        if conn:
            conn.close()
            print("\n[Test DB] Connection closed.")