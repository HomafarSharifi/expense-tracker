from database import get_connection


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
        
        cursor.execute('UPDATE expenses SET amount=%s, date=%s, reason=%s, category=%s WHERE id=%s;', (amount, date, reason, category, expense_id))
        connection.commit()
        return True
    except Exception as e:
        if connection is not None and connection.is_connected():
            connection.rollback()
        print(f"Failed to update expense: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def delete_expense(expense_id):
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute('DELETE FROM expenses WHERE id = %s;', (expense_id,))
        if cursor.rowcount == 0:
            print(f"No expense found with ID {expense_id}.")
            return False
        connection.commit()
        return True
    except Exception as e:
        if connection is not None and connection.is_connected():
            connection.rollback()
        print(f"Failed to delete the expense: {e}")
        return False
    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

def get_spending_by_category():
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute('SELECT category, sum(amount) AS total_amount FROM expenses GROUP BY category')
        result = cursor.fetchall()
    except Exception as e:
        connection.rollback()
        print(f'Failed to categorize due to: {e}')
        return []
    finally:
        cursor.close()
        connection.close()
    return result

def get_total_spending():
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute('SELECT SUM(amount) AS total_spending FROM expenses')
        result = cursor.fetchone()
    except Exception as e:
        connection.rollback()
        print(f"Failed to display expense: {e}")
        return []
    finally:
        cursor.close()
        connection.close()
    return result

def get_spending_over_time():
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute('SELECT date, SUM(amount) AS daily_total FROM expenses GROUP BY date ORDER BY date ASC;')
        result = cursor.fetchall()
    except Exception as e:
        connection.rollback()
        print(f"Failed to display expense: {e}")
        return []
    finally:
        cursor.close()
        connection.close()
    return result

def get_monthly_spending():
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT DATE_FORMAT(date, '%Y-%m') AS month, SUM(amount) AS monthly_total FROM expenses GROUP BY DATE_FORMAT(date, '%Y-%m') ORDER BY month ASC;")
        result = cursor.fetchall()
    except Exception as e:
        connection.rollback()
        print(f"Failed to get monthly expense: {e}")
        return []
    finally:
        cursor.close()
        connection.close()
    return result

def get_expenses():
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM expenses')
        result = cursor.fetchall()
    except Exception as e:
        connection.rollback()
        print(f"Failed to display expense: {e}")
        return []
    finally:
        cursor.close()
        connection.close()
    return result


def get_spending_by_date_range(start_date, end_date):
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT date, SUM(amount) AS daily_total FROM expenses WHERE date BETWEEN %s AND %s GROUP BY date ORDER BY date ASC;", (start_date, end_date))
        result = cursor.fetchall()
    except Exception as e:
        connection.rollback()
        print(f"Failed to get spending by date range: {e}")
        return []
    finally:
        cursor.close()
        connection.close()
    return result