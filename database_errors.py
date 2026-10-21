"""Friendly local-storage errors that avoid exposing data or file contents."""
import sqlite3


def database_error_help(error):
    if isinstance(error, sqlite3.IntegrityError):
        message = "A record did not meet the data rules. Review the amount, date, and category and try again."
    elif isinstance(error, sqlite3.OperationalError):
        message = "The local data file could not be opened. Check that you have access to your Windows profile folder and that the file is not locked."
    elif isinstance(error, sqlite3.DatabaseError):
        message = "The local data file may be damaged. Restore a recent backup or contact the project maintainer for help."
    else:
        message = "The requested data operation could not be completed. Check the values and try again."
    return message, type(error).__name__
