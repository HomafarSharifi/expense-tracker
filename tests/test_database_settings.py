from pathlib import Path
import tempfile
import unittest

from expense_tracker.storage import ExpenseStore, default_data_dir

tempfile.tempdir = str(Path(__file__).resolve().parents[1] / ".test-tmp")
Path(tempfile.tempdir).mkdir(exist_ok=True)


class LocalDatabaseSettingsTests(unittest.TestCase):
    def test_user_data_directory_uses_local_app_data_on_windows(self):
        self.assertEqual(default_data_dir().name, "ExpenseTracker")

    def test_database_file_can_be_reopened_and_settings_are_persisted(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "finance.sqlite3"
            store = ExpenseStore(path)
            store.add_expense(3, "2026-03-01", "", "Food")
            store.set_preference("language", "Dari")
            reopened = ExpenseStore(path)
            self.assertEqual(reopened.count_expenses(), 1)
            self.assertEqual(reopened.get_preference("language"), "Dari")


if __name__ == "__main__": unittest.main()
