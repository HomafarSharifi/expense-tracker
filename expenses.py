import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation

from database import get_connection


logger = logging.getLogger(__name__)


def validate_expense(amount, expense_date, reason, category):
    """Validate values against the database column limits before opening a connection."""
    try:
        numeric_amount = Decimal(str(amount))
        if not numeric_amount.is_finite() or numeric_amount <= 0:
            return False
        exceeds_column_limit = numeric_amount > Decimal("99999999.99")
        has_subcent_precision = (
            numeric_amount != numeric_amount.quantize(Decimal("0.01"))
        )
        if exceeds_column_limit or has_subcent_precision:
            return False
    except (InvalidOperation, TypeError, ValueError):
        return False
    try:
        datetime.strptime(str(expense_date), "%Y-%m-%d")
    except (TypeError, ValueError):
        return False
    if (
        not isinstance(category, str)
        or not category.strip()
        or len(category.strip()) > 40
    ):
        return False
    if reason is not None and (not isinstance(reason, str) or len(reason) > 100):
        return False
    return True


def validate_date_range(start_date, end_date):
    """Accept ISO dates only and require the beginning to be on/before the end."""
    try:
        start = datetime.strptime(str(start_date), "%Y-%m-%d").date()
        end = datetime.strptime(str(end_date), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return False
    return start <= end


def _close_resources(cursor, connection):
    # Cleanup should not hide the original query or commit error.
    for resource in (cursor, connection):
        if resource is not None:
            try:
                resource.close()
            except Exception:
                pass


def _fetch_all(query, params=None):
    connection = cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(query, params) if params is not None else cursor.execute(query)
        return cursor.fetchall()
    finally:
        _close_resources(cursor, connection)


def _fetch_one(query, params=None):
    connection = cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(query, params) if params is not None else cursor.execute(query)
        return cursor.fetchone()
    finally:
        _close_resources(cursor, connection)


def _positive_id(value):
    try:
        result = int(value)
        return result if result > 0 else None
    except (TypeError, ValueError):
        return None


def _rollback(connection):
    if connection is not None:
        try:
            connection.rollback()
        except Exception:
            pass


def add_expense(amount, expense_date, reason, category):
    if not validate_expense(amount, expense_date, reason, category):
        return False
    connection = cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO expenses (amount, date, reason, category) VALUES (%s, %s, %s, %s)",
            (amount, expense_date, reason or None, category.strip()),
        )
        connection.commit()
        return True
    except Exception as error:
        logger.error("Database operation failed (%s)", type(error).__name__)
        _rollback(connection)
        return False
    finally:
        _close_resources(cursor, connection)


def update_expense(expense_id, amount, expense_date, reason, category):
    expense_id = _positive_id(expense_id)
    if expense_id is None or not validate_expense(amount, expense_date, reason, category):
        return False
    connection = cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM expenses WHERE id = %s", (expense_id,))
        if cursor.fetchone() is None:
            return False
        cursor.execute(
            "UPDATE expenses SET amount = %s, date = %s, reason = %s, category = %s WHERE id = %s",
            (amount, expense_date, reason or None, category.strip(), expense_id),
        )
        connection.commit()
        return True
    except Exception as error:
        logger.error("Database operation failed (%s)", type(error).__name__)
        _rollback(connection)
        return False
    finally:
        _close_resources(cursor, connection)


def delete_expense(expense_id):
    expense_id = _positive_id(expense_id)
    if expense_id is None:
        return False
    connection = cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM expenses WHERE id = %s", (expense_id,))
        if cursor.rowcount == 0:
            return False
        connection.commit()
        return True
    except Exception as error:
        logger.error("Database operation failed (%s)", type(error).__name__)
        _rollback(connection)
        return False
    finally:
        _close_resources(cursor, connection)


def get_expenses():
    return _fetch_all(
        "SELECT id, amount, date, reason, category FROM expenses ORDER BY date DESC, id DESC"
    )


def get_categories():
    return _fetch_all(
        """SELECT DISTINCT category FROM expenses
           WHERE category IS NOT NULL AND TRIM(category) != ''
           ORDER BY category ASC"""
    )


def get_spending_by_category():
    return _fetch_all(
        """SELECT category, SUM(amount) AS total_amount FROM expenses
           GROUP BY category ORDER BY total_amount DESC, category ASC"""
    )


def get_total_spending():
    result = _fetch_one("SELECT COALESCE(SUM(amount), 0) FROM expenses")
    return result[0] if result else Decimal("0")


def get_spending_over_time():
    return _fetch_all(
        "SELECT date, SUM(amount) AS daily_total FROM expenses GROUP BY date ORDER BY date ASC"
    )


def get_monthly_spending():
    return _fetch_all(
        """SELECT DATE_FORMAT(date, '%Y-%m') AS month, SUM(amount) AS monthly_total
           FROM expenses GROUP BY DATE_FORMAT(date, '%Y-%m') ORDER BY month ASC"""
    )


def get_spending_by_date_range(start_date, end_date):
    if not validate_date_range(start_date, end_date):
        return []
    return _fetch_all(
        """SELECT date, SUM(amount) AS daily_total FROM expenses
           WHERE date BETWEEN %s AND %s GROUP BY date ORDER BY date ASC""",
        (start_date, end_date),
    )
def get_monthly_spending_by_category():
    """Return monthly totals split by category for the stacked analytics chart."""
    return _fetch_all(
        """SELECT DATE_FORMAT(date, '%Y-%m') AS month, category,
                  SUM(amount) AS monthly_total
           FROM expenses
           GROUP BY DATE_FORMAT(date, '%Y-%m'), category
           ORDER BY month ASC, category ASC"""
    )
