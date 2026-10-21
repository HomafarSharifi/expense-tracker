"""SQLite storage with explicit transactions and schema versioning.

Amounts are stored as integer minor units (paisa) to avoid floating point drift.
The database stays under the user's profile, separate from installed program files.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import json
import os
from pathlib import Path
import sqlite3
from typing import Iterator

APP_NAME = "ExpenseTracker"
BACKUP_FORMAT = "expense-tracker-backup"
LEGACY_BACKUP_FORMAT = "personal-expense-tracker-backup"
BACKUP_VERSION = 1


def default_data_dir() -> Path:
    """Return a per-user data directory without requiring an environment setup."""
    root = os.environ.get("LOCALAPPDATA")
    return (Path(root) if root else Path.home() / "AppData" / "Local") / APP_NAME


def default_database_path() -> Path:
    return default_data_dir() / "expenses.sqlite3"


def to_minor_units(amount: object) -> int:
    try:
        value = Decimal(str(amount))
        if not value.is_finite() or value <= 0 or value > Decimal("999999999999.99"):
            raise ValueError("Amount must be positive and within the supported limit.")
        quantized = value.quantize(Decimal("0.01"))
        if value != quantized:
            raise ValueError("Amount can have at most two decimal places.")
        return int(quantized * 100)
    except (InvalidOperation, TypeError) as error:
        raise ValueError("Enter a valid amount with up to two decimal places.") from error


def _iso_date(value: object) -> str:
    if isinstance(value, datetime):
        parsed = value.date()
    elif isinstance(value, date):
        parsed = value
    else:
        try:
            parsed = date.fromisoformat(str(value))
        except (TypeError, ValueError) as error:
            raise ValueError("Date must be a real date in YYYY-MM-DD format.") from error
    return parsed.isoformat()


def _validate_label(value: object, label: str, limit: int) -> str:
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > limit:
        raise ValueError(f"{label} must contain 1 to {limit} characters.")
    return value.strip()


class ExpenseStore:
    """Small SQLite repository. Each public operation owns its connection."""

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path is not None else default_database_path()
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(str(self.path), timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 10000")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connection() as db:
            db.execute("PRAGMA journal_mode = WAL")
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version > 2:
                raise RuntimeError("This database was created by a newer app version.")
            if version == 0:
                db.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS expenses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        amount_minor INTEGER NOT NULL CHECK(amount_minor > 0),
                        spent_on TEXT NOT NULL,
                        description TEXT NOT NULL DEFAULT '',
                        category TEXT NOT NULL,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(spent_on, id);
                    CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category);
                    CREATE TABLE IF NOT EXISTS income (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        month TEXT NOT NULL,
                        amount_minor INTEGER NOT NULL CHECK(amount_minor > 0),
                        source TEXT NOT NULL,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE INDEX IF NOT EXISTS idx_income_month ON income(month, id);
                    CREATE TABLE IF NOT EXISTS preferences (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL
                    );
                    PRAGMA user_version = 2;
                    """
                )
            elif version == 1:
                db.execute("CREATE TABLE IF NOT EXISTS preferences (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
                db.execute("PRAGMA user_version = 2")

    @staticmethod
    def _expense(row: sqlite3.Row | None) -> dict | None:
        if row is None:
            return None
        return {"id": row["id"], "amount": Decimal(row["amount_minor"]) / 100,
                "date": row["spent_on"], "description": row["description"],
                "category": row["category"]}

    @staticmethod
    def _income(row: sqlite3.Row | None) -> dict | None:
        if row is None:
            return None
        return {"id": row["id"], "month": row["month"],
                "amount": Decimal(row["amount_minor"]) / 100, "source": row["source"]}

    def add_expense(self, amount: object, spent_on: object, description: str, category: str) -> int:
        cents = to_minor_units(amount)
        day = _iso_date(spent_on)
        category = _validate_label(category, "Category", 80)
        description = "" if description is None else str(description).strip()
        if len(description) > 240:
            raise ValueError("Description cannot exceed 240 characters.")
        with self._connection() as db:
            cursor = db.execute(
                "INSERT INTO expenses(amount_minor, spent_on, description, category) VALUES (?, ?, ?, ?)",
                (cents, day, description, category),
            )
            return int(cursor.lastrowid)

    def update_expense(self, expense_id: int, amount: object, spent_on: object,
                       description: str, category: str) -> None:
        if int(expense_id) <= 0:
            raise ValueError("Expense ID must be a positive number.")
        cents, day = to_minor_units(amount), _iso_date(spent_on)
        category = _validate_label(category, "Category", 80)
        description = "" if description is None else str(description).strip()
        if len(description) > 240:
            raise ValueError("Description cannot exceed 240 characters.")
        with self._connection() as db:
            result = db.execute(
                "UPDATE expenses SET amount_minor=?, spent_on=?, description=?, category=? WHERE id=?",
                (cents, day, description, category, int(expense_id)),
            )
            if result.rowcount != 1:
                raise LookupError("That expense no longer exists.")

    def delete_expense(self, expense_id: int) -> None:
        with self._connection() as db:
            result = db.execute("DELETE FROM expenses WHERE id=?", (int(expense_id),))
            if result.rowcount != 1:
                raise LookupError("That expense no longer exists.")

    def get_expense(self, expense_id: int) -> dict | None:
        with self._connection() as db:
            row = db.execute("SELECT id, amount_minor, spent_on, description, category FROM expenses WHERE id=?", (int(expense_id),)).fetchone()
        return self._expense(row)

    def add_income(self, amount: object, month: object, source: str) -> int:
        cents = to_minor_units(amount)
        # Keep the exact period start: Gregorian months use day 1, while Afghan
        # Solar Hijri months begin on a different Gregorian date.
        month_text = _iso_date(month)
        source = _validate_label(source, "Income source", 100)
        with self._connection() as db:
            cursor = db.execute(
                "INSERT INTO income(month, amount_minor, source) VALUES (?, ?, ?)",
                (month_text, cents, source),
            )
            return int(cursor.lastrowid)

    def delete_income(self, income_id: int) -> None:
        with self._connection() as db:
            result = db.execute("DELETE FROM income WHERE id=?", (int(income_id),))
            if result.rowcount != 1:
                raise LookupError("That income record no longer exists.")

    def categories(self) -> list[str]:
        with self._connection() as db:
            rows = db.execute("SELECT DISTINCT category FROM expenses ORDER BY category COLLATE NOCASE").fetchall()
            return [row[0] for row in rows]

    def page_expenses(self, page: int = 1, page_size: int = 20, sort: str = "recent",
                      search: str = "", category: str | None = None,
                      start: object | None = None, end: object | None = None) -> tuple[list[dict], int]:
        page, page_size = max(1, int(page)), min(100, max(1, int(page_size)))
        ordering = {"recent": "spent_on DESC, id DESC", "oldest": "spent_on ASC, id ASC",
                    "highest": "amount_minor DESC, spent_on DESC", "lowest": "amount_minor ASC, spent_on DESC"}
        if sort not in ordering:
            raise ValueError("Unsupported sort order.")
        clauses, values = [], []
        if search.strip():
            clauses.append("(description LIKE ? ESCAPE '\\' OR category LIKE ? ESCAPE '\\')")
            escaped = search.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            values.extend((f"%{escaped}%", f"%{escaped}%"))
        if category:
            clauses.append("category = ?")
            values.append(category)
        if start:
            clauses.append("spent_on >= ?")
            values.append(_iso_date(start))
        if end:
            clauses.append("spent_on <= ?")
            values.append(_iso_date(end))
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        with self._connection() as db:
            total = db.execute("SELECT COUNT(*) FROM expenses" + where, values).fetchone()[0]
            rows = db.execute(
                "SELECT id, amount_minor, spent_on, description, category FROM expenses" + where +
                f" ORDER BY {ordering[sort]} LIMIT ? OFFSET ?",
                (*values, page_size, (page - 1) * page_size),
            ).fetchall()
        return [self._expense(row) for row in rows], int(total)

    def page_income(self, page: int = 1, page_size: int = 20, sort: str = "recent", search: str = "") -> tuple[list[dict], int]:
        ordering = {"recent": "month DESC, id DESC", "oldest": "month ASC, id ASC",
                    "highest": "amount_minor DESC, month DESC", "lowest": "amount_minor ASC, month DESC"}
        if sort not in ordering:
            raise ValueError("Unsupported sort order.")
        page, page_size = max(1, int(page)), min(100, max(1, int(page_size)))
        where, values = "", []
        if search.strip():
            literal = search.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            where, values = " WHERE source LIKE ? ESCAPE '\\'", [f"%{literal}%"]
        with self._connection() as db:
            total = db.execute("SELECT COUNT(*) FROM income" + where, values).fetchone()[0]
            rows = db.execute(
                f"SELECT id, month, amount_minor, source FROM income" + where + f" ORDER BY {ordering[sort]} LIMIT ? OFFSET ?",
                (*values, page_size, (page - 1) * page_size),
            ).fetchall()
        return [self._income(row) for row in rows], int(total)

    def summary(self, month: object | None = None, *, period_start: object | None = None, period_end: object | None = None) -> dict:
        selected_start = _iso_date(month) if month else date.today().replace(day=1).isoformat()
        month_text = selected_start[:7]
        start = _iso_date(period_start) if period_start else selected_start
        end_exclusive = (date.fromisoformat(_iso_date(period_end)) + __import__("datetime").timedelta(days=1)).isoformat() if period_end else (date.fromisoformat(start).replace(day=28) + __import__("datetime").timedelta(days=4)).replace(day=1).isoformat()
        with self._connection() as db:
            spending = db.execute("SELECT COALESCE(SUM(amount_minor),0) FROM expenses WHERE spent_on >= ? AND spent_on < ?", (start, end_exclusive)).fetchone()[0]
            # Income is stored at the selected calendar month's start date.
            # Sum by the same date interval as spending so switching between
            # Gregorian and Solar Hijri calendars does not hide a valid income.
            income = db.execute("SELECT COALESCE(SUM(amount_minor),0) FROM income WHERE month >= ? AND month < ?", (start, end_exclusive)).fetchone()[0]
            count = db.execute("SELECT COUNT(*) FROM expenses WHERE spent_on >= ? AND spent_on < ?", (start, end_exclusive)).fetchone()[0]
            totals = db.execute("SELECT category, SUM(amount_minor) total FROM expenses WHERE spent_on >= ? AND spent_on < ? GROUP BY category ORDER BY total DESC, category COLLATE NOCASE", (start, end_exclusive)).fetchall()
        return {"month": month_text, "income": Decimal(income) / 100,
                "spending": Decimal(spending) / 100, "remaining": Decimal(income - spending) / 100,
                "expense_count": int(count), "categories": [(r["category"], Decimal(r["total"]) / 100) for r in totals]}

    def page_months(self, page: int = 1, page_size: int = 12, sort: str = "recent", calendar: str = "Gregorian", search: str = "") -> tuple[list[dict], int]:
        ordering = {"recent": "month DESC", "oldest": "month ASC", "highest": "spending DESC", "lowest": "spending ASC"}
        if sort not in ordering or calendar not in {"Gregorian", "Afghan Solar Hijri"}:
            raise ValueError("Unsupported sort order.")
        page, page_size = max(1, int(page)), min(100, max(1, int(page_size)))
        with self._connection() as db:
            if calendar == "Gregorian":
                rows = db.execute("SELECT substr(spent_on,1,7) month, SUM(amount_minor) spending FROM expenses GROUP BY month").fetchall()
            else:
                daily = db.execute("SELECT spent_on, SUM(amount_minor) spending FROM expenses GROUP BY spent_on").fetchall()
        if calendar == "Afghan Solar Hijri":
            from jalali_calendar import month_key
            totals = {}
            for row in daily:
                key = month_key(date.fromisoformat(row["spent_on"]))
                totals[key] = totals.get(key, 0) + row["spending"]
            rows = [{"month": key, "spending": value} for key, value in totals.items()]
        values = [{"month": row["month"], "spending": Decimal(row["spending"]) / 100} for row in rows]
        if search.strip():
            query = search.strip().casefold()
            values = [row for row in values if query in row["month"].casefold()]
        if sort == "recent": values.sort(key=lambda row: row["month"], reverse=True)
        elif sort == "oldest": values.sort(key=lambda row: row["month"])
        elif sort == "highest": values.sort(key=lambda row: (row["spending"], row["month"]), reverse=True)
        else: values.sort(key=lambda row: (row["spending"], row["month"]))
        total = len(values)
        offset = (page - 1) * page_size
        return values[offset:offset + page_size], total

    def all_months(self) -> list[dict]:
        """Chronological chart series; the visible table remains paginated."""
        with self._connection() as db:
            rows = db.execute("SELECT substr(spent_on,1,7) month, SUM(amount_minor) spending FROM expenses GROUP BY month ORDER BY month ASC").fetchall()
        return [{"month": r["month"], "spending": Decimal(r["spending"]) / 100} for r in rows]

    def monthly_comparison(self, calendar: str = "Gregorian") -> list[dict]:
        if calendar not in {"Gregorian", "Afghan Solar Hijri"}:
            raise ValueError("Unsupported calendar.")
        with self._connection() as db:
            expenses = db.execute("SELECT spent_on, SUM(amount_minor) total FROM expenses GROUP BY spent_on").fetchall()
            income = db.execute("SELECT month, SUM(amount_minor) total FROM income GROUP BY month").fetchall()
        if calendar == "Afghan Solar Hijri":
            from jalali_calendar import month_key
            expense_key = lambda row: month_key(date.fromisoformat(row["spent_on"]))
            income_key = lambda row: month_key(date.fromisoformat(row["month"]))
        else:
            expense_key = lambda row: row["spent_on"][:7]
            income_key = lambda row: row["month"][:7]
        comparison = {}
        for row in expenses:
            key = expense_key(row)
            entry = comparison.setdefault(key, {"month": key, "spending": Decimal("0"), "income": Decimal("0")})
            entry["spending"] += Decimal(row["total"]) / 100
        for row in income:
            key = income_key(row)
            entry = comparison.setdefault(key, {"month": key, "spending": Decimal("0"), "income": Decimal("0")})
            entry["income"] = Decimal(row["total"]) / 100
        return [comparison[key] for key in sorted(comparison)]

    def spending_by_category(self, month: object | None = None) -> list[tuple[str, Decimal]]:
        with self._connection() as db:
            if month:
                start = _iso_date(month)[:7] + "-01"
                next_month = (date.fromisoformat(start).replace(day=28) + __import__("datetime").timedelta(days=4)).replace(day=1).isoformat()
                rows = db.execute("SELECT category, SUM(amount_minor) total FROM expenses WHERE spent_on >= ? AND spent_on < ? GROUP BY category ORDER BY total DESC, category COLLATE NOCASE", (start, next_month)).fetchall()
            else:
                rows = db.execute("SELECT category, SUM(amount_minor) total FROM expenses GROUP BY category ORDER BY total DESC, category COLLATE NOCASE").fetchall()
        return [(row["category"], Decimal(row["total"]) / 100) for row in rows]

    def all_expenses(self) -> list[dict]:
        return self.page_expenses(1, 100, "recent")[0] if self.count_expenses() <= 100 else self._all_expenses_unlimited()

    def _all_expenses_unlimited(self) -> list[dict]:
        with self._connection() as db:
            rows = db.execute("SELECT id, amount_minor, spent_on, description, category FROM expenses ORDER BY spent_on DESC, id DESC").fetchall()
        return [self._expense(row) for row in rows]

    def count_expenses(self) -> int:
        with self._connection() as db:
            return int(db.execute("SELECT COUNT(*) FROM expenses").fetchone()[0])

    def get_preference(self, key: str, default: str = "") -> str:
        with self._connection() as db:
            row = db.execute("SELECT value FROM preferences WHERE key=?", (key,)).fetchone()
            return row[0] if row else default

    def set_preference(self, key: str, value: str) -> None:
        if key not in {"language", "calendar"}:
            raise ValueError("Unsupported preference.")
        with self._connection() as db:
            db.execute("INSERT INTO preferences(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))

    def backup(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as db:
            expenses = [dict(row) for row in db.execute("SELECT id, amount_minor, spent_on, description, category FROM expenses ORDER BY id")]
            income = [dict(row) for row in db.execute("SELECT id, month, amount_minor, source FROM income ORDER BY id")]
        payload = {"format": BACKUP_FORMAT, "version": BACKUP_VERSION,
                   "created_at": datetime.now().astimezone().isoformat(),
                   "expenses": expenses, "income": income}
        temp = target.with_suffix(target.suffix + ".tmp")
        temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(target)
        return target

    def restore(self, path: str | Path) -> tuple[int, int]:
        source = Path(path)
        if source.stat().st_size > 100 * 1024 * 1024:
            raise ValueError("Backup is larger than the supported 100 MB limit.")
        try:
            payload = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError("Could not read this backup file.") from error
        if not isinstance(payload, dict):
            raise ValueError("Backup file must contain an Expense Tracker backup object.")
        if payload.get("format") not in {BACKUP_FORMAT, LEGACY_BACKUP_FORMAT}:
            raise ValueError("This is not a supported Expense Tracker backup.")
        if payload.get("version") not in {1}:
            raise ValueError("This backup version is not supported.")
        if not isinstance(payload.get("expenses", []), list) or not isinstance(payload.get("income", payload.get("monthly_income", [])), list):
            raise ValueError("Backup records must be JSON lists.")
        if len(payload.get("expenses", [])) > 1_000_000 or len(payload.get("income", payload.get("monthly_income", []))) > 1_000_000:
            raise ValueError("Backup is larger than the supported record limit.")
        expense_records, income_records = [], []
        for row in payload.get("expenses", []):
            if not isinstance(row, dict):
                raise ValueError("Backup contains an invalid expense record.")
            if "amount_minor" in row:
                if type(row["amount_minor"]) is not int:
                    raise ValueError("Backup contains an invalid expense amount.")
                cents = row["amount_minor"]
            else:
                cents = to_minor_units(row.get("amount"))
            if cents <= 0 or cents > 99_999_999_999_999:
                raise ValueError("Backup contains an invalid expense amount.")
            expense_records.append((cents, _iso_date(row.get("spent_on", row.get("date"))),
                                    str(row.get("description", row.get("reason", "")))[:240],
                                    _validate_label(row.get("category"), "Category", 80)))
        for row in payload.get("income", payload.get("monthly_income", [])):
            if not isinstance(row, dict):
                raise ValueError("Backup contains an invalid income record.")
            if "amount_minor" in row:
                if type(row["amount_minor"]) is not int:
                    raise ValueError("Backup contains an invalid income amount.")
                cents = row["amount_minor"]
            else:
                cents = to_minor_units(row.get("amount"))
            if cents <= 0 or cents > 99_999_999_999_999:
                raise ValueError("Backup contains an invalid income amount.")
            month = _iso_date(row.get("month", row.get("income_month")))
            source = _validate_label(row.get("source"), "Income source", 100)
            income_records.append((month, cents, source))
        with self._connection() as db:
            if db.execute("SELECT EXISTS(SELECT 1 FROM expenses) OR EXISTS(SELECT 1 FROM income)").fetchone()[0]:
                raise ValueError("Restore is only allowed when this profile has no records. Back up first.")
            db.executemany("INSERT INTO expenses(amount_minor, spent_on, description, category) VALUES (?, ?, ?, ?)", expense_records)
            db.executemany("INSERT INTO income(month, amount_minor, source) VALUES (?, ?, ?)", income_records)
        return len(expense_records), len(income_records)

