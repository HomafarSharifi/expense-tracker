from decimal import Decimal
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import data_backup


def sample_payload():
    return {
        "format": data_backup.FORMAT_NAME,
        "version": data_backup.FORMAT_VERSION,
        "created_at_utc": "2026-10-19T00:00:00+00:00",
        "expenses": [
            {
                "id": 7,
                "amount": "123.45",
                "date": "2026-10-16",
                "reason": "خرید نان",
                "category": "FOOD",
            }
        ],
        "monthly_income": [
            {
                "id": 3,
                "income_month": "2026-10-01",
                "source": "Salary",
                "amount": "2500.00",
            }
        ],
    }


class BackupFileTests(unittest.TestCase):
    def test_validates_utf8_backup_records(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as directory:
            path = Path(directory) / "backup.json"
            path.write_text(json.dumps(sample_payload(), ensure_ascii=False), encoding="utf-8")
            expenses, income = data_backup._load_and_validate_backup(path)
        self.assertEqual(expenses[0], (7, Decimal("123.45"), "2026-10-16", "خرید نان", "FOOD"))
        self.assertEqual(income[0], (3, "2026-10-01", "Salary", Decimal("2500.00")))

    def test_rejects_corrupt_backup_records_before_connecting(self):
        payload = sample_payload()
        payload["expenses"][0]["date"] = "not-a-date"
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as directory:
            path = Path(directory) / "bad.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid expense"):
                data_backup._load_and_validate_backup(path)

    def test_restore_inserts_records_when_both_tables_are_empty(self):
        cursor, connection = Mock(), Mock()
        connection.cursor.return_value = cursor
        cursor.fetchone.side_effect = [(0,), (0,)]
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as directory:
            path = Path(directory) / "backup.json"
            path.write_text(json.dumps(sample_payload()), encoding="utf-8")
            with patch.object(data_backup, "get_connection", return_value=connection):
                self.assertEqual(data_backup.restore_database(path), (1, 1))
        self.assertEqual(cursor.executemany.call_count, 2)
        connection.commit.assert_called_once()

    def test_restore_refuses_non_empty_tables_without_writing(self):
        cursor, connection = Mock(), Mock()
        connection.cursor.return_value = cursor
        cursor.fetchone.side_effect = [(1,), (0,)]
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as directory:
            path = Path(directory) / "backup.json"
            path.write_text(json.dumps(sample_payload()), encoding="utf-8")
            with patch.object(data_backup, "get_connection", return_value=connection):
                with self.assertRaisesRegex(ValueError, "both database tables must be empty"):
                    data_backup.restore_database(path)
        cursor.executemany.assert_not_called()
        connection.rollback.assert_called_once()
        connection.commit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
