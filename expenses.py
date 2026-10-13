from database import get_connection
from datetime import datetime
from decimal import Decimal, InvalidOperation


def validate_expense(amount, expense_date, reason, category):
    try:
        numeric_amount = Decimal(str(amount))
        if not numeric_amount.is_finite() or numeric_amount <= 0:
            return False
        if numeric_amount > Decimal("99999999.99"):
            return False
    except (InvalidOperation, TypeError, ValueError):
        return False

    try:
        datetime.strptime(str(expense_date), "%Y-%m-%d")
    except (TypeError, ValueError):
        return False

    if not isinstance(category, str) or not category.strip():
        return False

    if reason is not None:
        if not isinstance(reason, str) or len(reason) > 100:
            return False

    return True


def _fetch_all(query, params=None):
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        if params is None:
            cursor.execute(query)
        else:
            cursor.execute(query, params)

        return cursor.fetchall()

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


def _fetch_one(query, params=None):
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        if params is None:
            cursor.execute(query)
        else:
            cursor.execute(query, params)

        return cursor.fetchone()

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


def add_expense(amount, date, reason, category):
    if not validate_expense(amount, date, reason, category):
        print("Invalid expense data.")
        return False

    # Validate the date format.
    try:
        datetime.strptime(str(date), "%Y-%m-%d")
    except (TypeError, ValueError):
        print("Date must use YYYY-MM-DD format.")
        return False

    # Validate the category.
    if not isinstance(category, str) or not category.strip():
        print("Category cannot be empty.")
        return False

    # Validate the optional description.
    if reason is not None and len(reason) > 100:
        print("Reason cannot exceed 100 characters.")
        return False
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO expenses (amount, date, reason, category) VALUES(%s, %s, %s, %s)", (amount, date, reason, category))
        connection.commit()
        return True
    except Exception as e:
        if connection is not None and connection.is_connected():
            connection.rollback()
        print(f"Failed to add expense: {e}")
        return False

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()


def update_expense(expense_id, amount, date, reason, category):
    if not validate_expense(amount, date, reason, category):
        print("Invalid expense data.")
        return False

    try:
        expense_id = int(expense_id)
        if expense_id <= 0:
            return False
    except (TypeError, ValueError):
        return False

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT id FROM expenses WHERE id = %s",
            (expense_id,)
        )

        if cursor.fetchone() is None:
            print(f"No expense found with ID {expense_id}.")
            return False

        cursor.execute(
            """
            UPDATE expenses
            SET amount = %s, date = %s, reason = %s, category = %s
            WHERE id = %s
            """,
            (amount, date, reason, category.strip(), expense_id)
        )

        connection.commit()
        return True

    except Exception as error:
        if connection is not None and connection.is_connected():
            connection.rollback()

        print(f"Failed to update expense: {error}")
        return False

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()


def delete_expense(expense_id):
    try:
        expense_id = int(expense_id)
        if expense_id <= 0:
            return False
    except (TypeError, ValueError):
        return False

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            "DELETE FROM expenses WHERE id = %s",
            (expense_id,)
        )

        if cursor.rowcount == 0:
            print(f"No expense found with ID {expense_id}.")
            return False

        connection.commit()
        return True

    except Exception as error:
        if connection is not None and connection.is_connected():
            connection.rollback()

        print(f"Failed to delete expense: {error}")
        return False

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

def get_expenses():
    return _fetch_all(
        """
        SELECT id, amount, date, reason, category
        FROM expenses
        ORDER BY date DESC, id DESC
        """
    )


def get_spending_by_category():
    return _fetch_all(
        """
        SELECT category, SUM(amount) AS total_amount
        FROM expenses
        GROUP BY category
        ORDER BY total_amount DESC
        """
    )


def get_total_spending():
    result = _fetch_one(
        """
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
        """
    )

    return result[0]


def get_spending_over_time():
    return _fetch_all(
        """
        SELECT date, SUM(amount) AS daily_total
        FROM expenses
        GROUP BY date
        ORDER BY date ASC
        """
    )


def get_monthly_spending():
    return _fetch_all(
        """
        SELECT DATE_FORMAT(date, '%Y-%m') AS month,
               SUM(amount) AS monthly_total
        FROM expenses
        GROUP BY DATE_FORMAT(date, '%Y-%m')
        ORDER BY month ASC
        """
    )


def get_spending_by_date_range(start_date, end_date):
    return _fetch_all(
        """
        SELECT date, SUM(amount) AS daily_total
        FROM expenses
        WHERE date BETWEEN %s AND %s
        GROUP BY date
        ORDER BY date ASC
        """,
        (start_date, end_date)
    )