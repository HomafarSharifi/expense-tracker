"""Create and safely restore JSON backups of expense-tracker database records."""

import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import sys

from database import get_connection
from database_errors import database_error_help
from expenses import validate_expense, validate_income


FORMAT_NAME = "personal-expense-tracker-backup"
FORMAT_VERSION = 1


def backup_database(destination=None):
    """Write an atomic, UTF-8 backup containing expenses and monthly income."""
    backup_dir = Path(__file__).resolve().parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    if destination is None:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        destination = backup_dir / f"expense-tracker-{stamp}.json"
    else:
        destination = Path(destination).expanduser().resolve()
    if destination.exists():
        raise FileExistsError(f"Backup already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)

    connection = cursor = None
    temporary = destination.with_name(destination.name + ".tmp")
    temporary_created = False
    try:
        connection = get_connection()
        connection.start_transaction(consistent_snapshot=True, readonly=True)
        cursor = connection.cursor()
        cursor.execute("SELECT id, amount, date, reason, category FROM expenses ORDER BY id")
        expense_rows = cursor.fetchall()
        cursor.execute(
            "SELECT id, income_month, source, amount FROM monthly_income ORDER BY id"
        )
        income_rows = cursor.fetchall()
        payload = {
            "format": FORMAT_NAME,
            "version": FORMAT_VERSION,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "expenses": [
                {
                    "id": int(row[0]),
                    "amount": str(row[1]),
                    "date": row[2].isoformat(),
                    "reason": row[3],
                    "category": row[4],
                }
                for row in expense_rows
            ],
            "monthly_income": [
                {
                    "id": int(row[0]),
                    "income_month": row[1].isoformat(),
                    "source": row[2],
                    "amount": str(row[3]),
                }
                for row in income_rows
            ],
        }
        with temporary.open("x", encoding="utf-8", newline="\n") as backup_file:
            temporary_created = True
            json.dump(payload, backup_file, ensure_ascii=False, indent=2)
            backup_file.write("\n")
        temporary.replace(destination)
        return destination
    except Exception:
        if temporary_created and temporary.exists():
            temporary.unlink()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()


def _load_and_validate_backup(source):
    source = Path(source).expanduser().resolve()
    with source.open("r", encoding="utf-8") as backup_file:
        payload = json.load(backup_file)
    if (
        not isinstance(payload, dict)
        or payload.get("format") != FORMAT_NAME
        or payload.get("version") != FORMAT_VERSION
        or not isinstance(payload.get("expenses"), list)
        or not isinstance(payload.get("monthly_income"), list)
    ):
        raise ValueError("This is not a supported expense-tracker backup.")

    expenses, income = [], []
    seen_expense_ids, seen_income_ids = set(), set()
    for item in payload["expenses"]:
        if not isinstance(item, dict):
            raise ValueError("The backup contains an invalid expense record.")
        record_id = _record_id(item.get("id"), seen_expense_ids)
        amount = _positive_amount(item.get("amount"))
        expense_date = item.get("date")
        category = item.get("category")
        reason = item.get("reason")
        if not validate_expense(amount, expense_date, reason, category):
            raise ValueError(f"The backup contains invalid expense record {record_id}.")
        expenses.append(
            (record_id, amount, expense_date, reason, category.strip())
        )

    for item in payload["monthly_income"]:
        if not isinstance(item, dict):
            raise ValueError("The backup contains an invalid income record.")
        record_id = _record_id(item.get("id"), seen_income_ids)
        amount = _positive_amount(item.get("amount"))
        income_month = item.get("income_month")
        source_name = item.get("source")
        if not validate_income(amount, income_month, source_name, exact=True):
            raise ValueError(f"The backup contains invalid income record {record_id}.")
        income.append((record_id, income_month, source_name.strip(), amount))
    return expenses, income


def _record_id(value, seen):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0 or value in seen:
        raise ValueError("The backup contains a missing, invalid, or duplicate record ID.")
    seen.add(value)
    return value


def _positive_amount(value):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("The backup contains an invalid amount.") from None
    if not amount.is_finite() or amount <= 0 or amount > Decimal("99999999.99"):
        raise ValueError("The backup contains an invalid amount.")
    return amount


def restore_database(source):
    """Restore only to an empty pair of tables; existing records are never replaced."""
    expenses, income = _load_and_validate_backup(source)
    connection = cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM expenses")
        expense_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM monthly_income")
        income_count = cursor.fetchone()[0]
        if expense_count or income_count:
            raise ValueError(
                "Restore stopped: both database tables must be empty. "
                "Back up the current database first, then restore into an empty database."
            )
        if expenses:
            cursor.executemany(
                "INSERT INTO expenses (id, amount, date, reason, category) VALUES (%s, %s, %s, %s, %s)",
                expenses,
            )
        if income:
            cursor.executemany(
                "INSERT INTO monthly_income (id, income_month, source, amount) VALUES (%s, %s, %s, %s)",
                income,
            )
        connection.commit()
        return len(expenses), len(income)
    except Exception:
        if connection is not None:
            connection.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Back up or safely restore this app's MySQL/MariaDB records."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    backup_parser = commands.add_parser("backup", help="create a timestamped backup")
    backup_parser.add_argument("--output", help="optional output .json path")
    restore_parser = commands.add_parser("restore", help="restore into empty tables only")
    restore_parser.add_argument("backup_file", help="path to a backup JSON file")
    args = parser.parse_args(argv)

    try:
        if args.command == "backup":
            path = backup_database(args.output)
            print(f"Backup created: {path}")
        else:
            expense_count, income_count = restore_database(args.backup_file)
            print(
                f"Restore completed: {expense_count} expenses and "
                f"{income_count} income entries."
            )
    except (OSError, ValueError) as error:
        print(f"Backup operation stopped: {error}", file=sys.stderr)
        return 1
    except Exception as error:
        message, diagnostic = database_error_help(error)
        print(f"Backup operation stopped: {message}\n{diagnostic}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
