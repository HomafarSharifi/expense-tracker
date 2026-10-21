import json
from decimal import Decimal
from pathlib import Path
import tempfile
import unittest

from expense_tracker.storage import ExpenseStore

tempfile.tempdir = str(Path(__file__).resolve().parents[1] / ".test-tmp")
Path(tempfile.tempdir).mkdir(exist_ok=True)


class BackupMigrationTests(unittest.TestCase):
    def test_restores_existing_mysql_json_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "legacy.json"
            source.write_text(json.dumps({
                "format": "personal-expense-tracker-backup", "version": 1,
                "expenses": [{"id": 7, "amount": "123.45", "date": "2026-10-16", "reason": "خرید نان", "category": "FOOD"}],
                "monthly_income": [{"id": 3, "income_month": "2026-10-01", "source": "Salary", "amount": "2500.00"}],
            }, ensure_ascii=False), encoding="utf-8")
            store = ExpenseStore(Path(directory) / "new.sqlite3")
            self.assertEqual(store.restore(source), (1, 1))
            expense = store.get_expense(1)
            self.assertEqual(expense["amount"], Decimal("123.45"))
            self.assertEqual(expense["description"], "خرید نان")
            self.assertEqual(store.page_income()[0][0]["source"], "Salary")

    def test_refuses_restore_over_existing_records(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ExpenseStore(Path(directory) / "new.sqlite3")
            store.add_expense(1, "2026-01-01", "", "Food")
            source = Path(directory) / "backup.json"
            source.write_text(json.dumps({"format":"expense-tracker-backup", "version":1, "expenses":[], "income":[]}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "no records"):
                store.restore(source)

    def test_rejects_invalid_backup_before_insert(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ExpenseStore(Path(directory) / "new.sqlite3")
            source = Path(directory) / "backup.json"
            source.write_text(json.dumps({"format":"expense-tracker-backup", "version":1, "expenses":[{"amount":"NaN", "date":"2026-01-01", "category":"Food"}], "income":[]}), encoding="utf-8")
            with self.assertRaises(ValueError): store.restore(source)
            self.assertEqual(store.count_expenses(), 0)

    def test_creates_and_restores_own_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            original = ExpenseStore(Path(directory) / "original.sqlite3")
            original.add_expense("9.50", "2026-02-01", "Bus", "Travel")
            backup = original.backup(Path(directory) / "backup.json")
            restored = ExpenseStore(Path(directory) / "restored.sqlite3")
            self.assertEqual(restored.restore(backup), (1, 0))
            self.assertEqual(restored.get_expense(1)["amount"], 9.5)


if __name__ == "__main__": unittest.main()
