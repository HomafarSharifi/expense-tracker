"""Local database entry point. MySQL is not used by this release."""
from pathlib import Path
from expense_tracker.storage import ExpenseStore


def get_store(path: str | Path | None = None) -> ExpenseStore:
    return ExpenseStore(path)


def get_connection(path: str | Path | None = None):
    """Return a plain SQLite connection for migration tools; normal code uses ExpenseStore."""
    store = ExpenseStore(path)
    import sqlite3
    connection = sqlite3.connect(str(store.path), timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    return connection
