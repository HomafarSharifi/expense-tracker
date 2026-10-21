from datetime import date
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from expense_tracker.storage import ExpenseStore
from tools.migrate_mysql_v1 import export_backup


PROJECT = Path(__file__).resolve().parents[1]
tempfile.tempdir = str(PROJECT / ".test-tmp")
Path(tempfile.tempdir).mkdir(exist_ok=True)


class ReadOnlyMySqlMigrationTests(unittest.TestCase):
    def test_exports_both_v1_tables_into_new_app_format(self):
        cursor, connection = Mock(), Mock()
        cursor.fetchall.side_effect = [
            [{"id": 4, "amount": "12.50", "date": date(2026, 1, 2), "reason": "نان", "category": "Food"}],
            [{"id": 2, "income_month": date(2026, 1, 1), "source": "Salary", "amount": "100.00"}],
        ]
        connection.cursor.return_value = cursor
        with tempfile.TemporaryDirectory() as directory:
            backup = Path(directory) / "old.json"
            self.assertEqual(export_backup(connection, backup), (1, 1))
            payload = json.loads(backup.read_text(encoding="utf-8"))
            self.assertEqual(payload["format"], "personal-expense-tracker-backup")
            self.assertNotIn("password", repr(payload).lower())
            store = ExpenseStore(Path(directory) / "new.sqlite3")
            self.assertEqual(store.restore(backup), (1, 1))
            self.assertEqual(store.get_expense(1)["description"], "نان")
        self.assertEqual(cursor.execute.call_count, 2)
        cursor.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
