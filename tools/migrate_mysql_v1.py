"""Export the retired MySQL v1 tables as an importable JSON migration backup.

This optional tool is the only part of v2 that talks to MySQL. It performs
read-only SELECTs and never includes credentials in the backup or logs.
"""

from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
from decimal import Decimal
import getpass
import json
import os
from pathlib import Path
import sys

FORMAT = "personal-expense-tracker-backup"


def export_backup(connection, target: Path) -> tuple[int, int]:
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, amount, date, reason, category FROM expenses ORDER BY id")
        expenses = cursor.fetchall()
        cursor.execute("SELECT id, income_month, source, amount FROM monthly_income ORDER BY id")
        income = cursor.fetchall()
    finally:
        cursor.close()
    payload = {
        "format": FORMAT,
        "version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "expenses": [{
            "id": int(row["id"]), "amount": str(row["amount"]),
            "date": row["date"].isoformat() if isinstance(row["date"], (date, datetime)) else str(row["date"]),
            "reason": row.get("reason") or "", "category": row["category"],
        } for row in expenses],
        "monthly_income": [{
            "id": int(row["id"]), "income_month": row["income_month"].isoformat() if isinstance(row["income_month"], (date, datetime)) else str(row["income_month"]),
            "source": row["source"], "amount": str(row["amount"]),
        } for row in income],
    }
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(target)
    return len(expenses), len(income)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Read old MySQL tables and create a backup for the new offline app.")
    parser.add_argument("--host", default=os.getenv("EXPENSE_DB_HOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.getenv("EXPENSE_DB_PORT", "3306")))
    parser.add_argument("--user", default=os.getenv("EXPENSE_DB_USER", "root"))
    parser.add_argument("--database", default=os.getenv("EXPENSE_DB_NAME", "expense_tracker"))
    parser.add_argument("--output", type=Path, default=Path("legacy-expense-tracker-backup.json"))
    args = parser.parse_args(argv)
    try:
        import mysql.connector
    except ImportError:
        print("One-time migration needs mysql-connector-python. Install it with: python -m pip install mysql-connector-python", file=sys.stderr)
        return 2
    password = os.getenv("EXPENSE_DB_PASSWORD")
    if password is None:
        password = getpass.getpass(f"MySQL password for {args.user}@{args.host}: ")
    connection = None
    try:
        connection = mysql.connector.connect(host=args.host, port=args.port, user=args.user,
                                             password=password, database=args.database,
                                             connection_timeout=6)
        counts = export_backup(connection, args.output)
        print(f"Read-only migration backup created: {args.output} ({counts[0]} expenses, {counts[1]} income records).")
        print("Keep this unencrypted financial data private. Restore it from Settings in the new app.")
        return 0
    except Exception as error:
        print(f"Migration export failed ({type(error).__name__}). Check that MySQL is running and both v1 tables exist.", file=sys.stderr)
        return 2
    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
