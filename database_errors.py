def database_error_help(error):
    """Turn common MySQL startup errors into actionable, secret-safe guidance."""
    code = getattr(error, "errno", None)
    detail = str(getattr(error, "msg", ""))
    if code in (2002, 2003, 2005, 2006):
        message = (
            "Could not connect to the configured MySQL server. Start MySQL/MariaDB "
            "and verify EXPENSE_DB_HOST and EXPENSE_DB_PORT."
        )
    elif code == 1045:
        message = (
            "MySQL rejected the login. Verify EXPENSE_DB_USER and "
            "EXPENSE_DB_PASSWORD."
        )
    elif code == 1049:
        message = (
            "The configured database does not exist. Create expense_tracker or "
            "set EXPENSE_DB_NAME to the correct database."
        )
    elif code == 1044:
        message = (
            "The database account lacks permission for this database. Ask the "
            "database administrator to grant the app account access to expense_tracker."
        )
    elif code == 1146 and "monthly_income" in detail:
        message = (
            "The monthly_income table is missing from the database the app "
            "connected to. Run income.sql against that same database."
        )
    elif code == 1146 and "expenses" in detail:
        message = (
            "The expenses table is missing from the database the app connected "
            "to. Import expenses.sql, then run income.sql."
        )
    elif code == 1146:
        message = (
            "A required table is missing. Check that your SQL file was run "
            "against the same database named by EXPENSE_DB_NAME."
        )
    elif code == 1054:
        message = (
            "The database schema does not match this app version. Review the "
            "SQL setup instructions in README.md before changing any tables."
        )
    elif code in (1205, 1213):
        message = (
            "The database was busy and cancelled this request. Refresh and try again."
        )
    elif code in (2013,):
        message = (
            "The connection to MySQL was interrupted. Check that the database "
            "server is running, then refresh and try again."
        )
    elif isinstance(error, ValueError):
        message = (
            "A database setting is invalid. Check that the database port and "
            "connection timeout are whole numbers."
        )
    else:
        message = (
            "The app could not complete the database request. Refresh and try "
            "again; if it continues, review the database diagnostic."
        )
    diagnostic = f"{type(error).__name__}"
    if code is not None:
        diagnostic += f" · MySQL error {code}"
    if code == 1146 and detail:
        diagnostic += f" · {detail}"
    return message, diagnostic
