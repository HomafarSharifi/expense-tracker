import os
import mysql.connector


def get_connection():
    """Create a MySQL connection from environment-based configuration."""
    return mysql.connector.connect(
        host=os.getenv("EXPENSE_DB_HOST", "localhost"),
        port=int(os.getenv("EXPENSE_DB_PORT", "3306")),
        user=os.getenv("EXPENSE_DB_USER", "root"),
        password=os.getenv("EXPENSE_DB_PASSWORD", ""),
        database=os.getenv("EXPENSE_DB_NAME", "expense_tracker"),
        connection_timeout=int(os.getenv("EXPENSE_DB_CONNECT_TIMEOUT", "5")),
    )
