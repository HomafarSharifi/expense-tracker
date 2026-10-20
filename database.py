import os
import mysql.connector


def _setting(name, default):
    """Read environment overrides first, then local/deployed Streamlit secrets."""
    if name in os.environ:
        return os.environ[name]
    try:
        import streamlit as st

        return st.secrets.get(name, default)
    except FileNotFoundError:
        return default


def get_public_connection_settings():
    """Return display-safe connection details without exposing the password."""
    return {
        "host": _setting("EXPENSE_DB_HOST", "localhost"),
        "port": _setting("EXPENSE_DB_PORT", "3306"),
        "user": _setting("EXPENSE_DB_USER", "root"),
        "database": _setting("EXPENSE_DB_NAME", "expense_tracker"),
    }


def get_connection():
    """Create a MySQL connection from environment-based configuration."""
    return mysql.connector.connect(
        host=_setting("EXPENSE_DB_HOST", "localhost"),
        port=int(_setting("EXPENSE_DB_PORT", "3306")),
        user=_setting("EXPENSE_DB_USER", "root"),
        password=_setting("EXPENSE_DB_PASSWORD", ""),
        database=_setting("EXPENSE_DB_NAME", "expense_tracker"),
        connection_timeout=int(_setting("EXPENSE_DB_CONNECT_TIMEOUT", "5")),
    )
