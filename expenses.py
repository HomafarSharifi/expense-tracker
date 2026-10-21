"""SQLite-backed compatibility helpers for simple scripts. Prefer ExpenseStore for new code."""

from datetime import date
from decimal import Decimal

from expense_tracker.storage import ExpenseStore, to_minor_units


def validate_expense(amount, expense_date, reason, category):
    try:
        to_minor_units(amount)
        date.fromisoformat(str(expense_date)[:10])
        return isinstance(category, str) and 0 < len(category.strip()) <= 80 and len(str(reason or "")) <= 240
    except (TypeError, ValueError):
        return False


def validate_date_range(start_date, end_date):
    try:
        return date.fromisoformat(str(start_date)[:10]) <= date.fromisoformat(str(end_date)[:10])
    except (TypeError, ValueError):
        return False


def add_expense(amount, expense_date, reason, category):
    try: ExpenseStore().add_expense(amount, expense_date, reason, category); return True
    except (ValueError, OSError): return False


def update_expense(expense_id, amount, expense_date, reason, category):
    try: ExpenseStore().update_expense(expense_id, amount, expense_date, reason, category); return True
    except (ValueError, LookupError, OSError): return False


def delete_expense(expense_id):
    try: ExpenseStore().delete_expense(expense_id); return True
    except (ValueError, LookupError, OSError): return False


def get_expenses():
    return [(r["id"], r["amount"], r["date"], r["description"], r["category"]) for r in ExpenseStore().all_expenses()]


def get_categories(): return [(value,) for value in ExpenseStore().categories()]

def get_spending_by_category(): return ExpenseStore().spending_by_category()
def get_total_spending(): return sum((item[1] for item in ExpenseStore().spending_by_category()), Decimal("0"))
def get_monthly_spending_totals(): return [(r["month"], r["spending"]) for r in ExpenseStore().all_months()]
