from database import get_connection


def add_expense(amount, date, reason, category):
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("INSERT INTO expenses (amount, date, reason, category) VALUES(%s, %s, %s, %s)", (amount, date, reason, category))
        connection.commit()
    except Exception as e:
        connection.rollback()
        print(f"Failed to add expense: {e}")

    finally:
        cursor.close()
        connection.close()

def update_expense(expense_id, amount, date, reason, category):
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute('UPDATE expenses SET amount=%s, date=%s, reason=%s, category=%s WHERE id=%s;', (amount, date, reason, category, expense_id))
        connection.commit()
    except Exception as e:
        connection.rollback()
        print(f"Failed to update expense: {e}")
    finally:
        cursor.close()
        connection.close()

def delete_expense(expense_id):
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute('DELETE FROM expenses WHERE id = %s;', (expense_id,))
        connection.commit()
    except Exception as e:
        connection.rollback()
        print(f"Failed to delete the expense: {e}")
    finally:
        cursor.close()
        connection.close()

def get_spending_by_category():
    connection = get_connection()
    cursor = connection.cursor()
    try:
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
    connection = get_connection()
    cursor = connection.cursor()
    try:
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
    connection = get_connection()
    cursor = connection.cursor()
    try:
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

def get_expenses():
    connection = get_connection()
    cursor = connection.cursor()
    try:
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