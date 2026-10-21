"""Command line interface for automation, testing, and technical users."""

from __future__ import annotations

import argparse
from datetime import date
from decimal import Decimal
import json
from pathlib import Path
import sqlite3
import sys

from database_errors import database_error_help
from .storage import ExpenseStore, default_database_path


def money(value: Decimal) -> str:
    return f"AFN {value:,.2f}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="expense-tracker", description="Offline personal expense and income tracker")
    parser.add_argument("--db", type=Path, help="Use a specific SQLite database file (defaults to your user data folder).")
    commands = parser.add_subparsers(dest="command")
    add = commands.add_parser("add", help="Add an expense")
    add.add_argument("amount"); add.add_argument("date", help="YYYY-MM-DD")
    add.add_argument("category"); add.add_argument("description", nargs="?", default="")
    update = commands.add_parser("update", help="Edit an expense")
    update.add_argument("id", type=int); update.add_argument("amount"); update.add_argument("date")
    update.add_argument("category"); update.add_argument("description", nargs="?", default="")
    delete = commands.add_parser("delete", help="Delete an expense")
    delete.add_argument("id", type=int)
    listing = commands.add_parser("list", help="List expenses")
    listing.add_argument("--page", type=int, default=1); listing.add_argument("--limit", type=int, default=20)
    listing.add_argument("--sort", choices=("recent", "oldest", "highest", "lowest"), default="recent")
    listing.add_argument("--search", default="")
    summary = commands.add_parser("summary", help="Show the selected month's income and spending")
    summary.add_argument("--month", default=date.today().strftime("%Y-%m"), help="YYYY-MM")
    income = commands.add_parser("income", help="Add monthly income")
    income.add_argument("amount"); income.add_argument("month", help="YYYY-MM")
    income.add_argument("source")
    backup = commands.add_parser("backup", help="Create a private JSON backup")
    backup.add_argument("path", nargs="?", type=Path)
    restore = commands.add_parser("restore", help="Restore a supported JSON backup into an empty profile")
    restore.add_argument("path", type=Path)
    export = commands.add_parser("export", help="Export expenses as CSV")
    export.add_argument("path", type=Path)
    return parser


def _table(rows: list[dict]) -> str:
    if not rows:
        return "No expenses found."
    columns = ("id", "date", "amount", "category", "description")
    rendered = [[str(row[key]) if key != "amount" else money(row[key]) for key in columns] for row in rows]
    widths = [max(len(label), *(len(row[index]) for row in rendered)) for index, label in enumerate(columns)]
    line = "  ".join(label.upper().ljust(widths[index]) for index, label in enumerate(columns))
    divider = "  ".join("-" * width for width in widths)
    return "\n".join((line, divider, *("  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)) for row in rendered)))


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        print(f"\nLocal data file: {args.db or default_database_path()}")
        return 0
    try:
        store = ExpenseStore(args.db)
        if args.command == "add":
            row_id = store.add_expense(args.amount, args.date, args.description, args.category)
            print(f"Expense #{row_id} saved.")
        elif args.command == "update":
            store.update_expense(args.id, args.amount, args.date, args.description, args.category)
            print(f"Expense #{args.id} updated.")
        elif args.command == "delete":
            store.delete_expense(args.id)
            print(f"Expense #{args.id} deleted.")
        elif args.command == "list":
            rows, total = store.page_expenses(args.page, args.limit, args.sort, args.search)
            print(_table(rows)); print(f"\nPage {args.page} · {len(rows)} shown · {total} total")
        elif args.command == "summary":
            value = store.summary(args.month + "-01")
            print(f"{value['month']}  |  Income {money(value['income'])}  |  Spending {money(value['spending'])}  |  Remaining {money(value['remaining'])}")
            for category, total in value["categories"]:
                print(f"  {category}: {money(total)}")
        elif args.command == "income":
            row_id = store.add_income(args.amount, args.month + "-01", args.source)
            print(f"Income #{row_id} saved.")
        elif args.command == "backup":
            target = args.path or (default_database_path().parent / "backups" / f"expense-tracker-{date.today().isoformat()}.json")
            print(f"Backup saved: {store.backup(target)}")
        elif args.command == "restore":
            expense_count, income_count = store.restore(args.path)
            print(f"Restored {expense_count} expenses and {income_count} income records.")
        elif args.command == "export":
            from .reports import export_csv
            count = export_csv(store, args.path)
            print(f"Exported {count} expenses: {args.path}")
        return 0
    except sqlite3.Error as error:
        message, _diagnostic = database_error_help(error)
        print(f"Error: {message}", file=sys.stderr)
        return 2
    except (ValueError, LookupError, OSError, RuntimeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(run())
