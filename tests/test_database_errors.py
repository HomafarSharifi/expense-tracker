import csv
from pathlib import Path
import tempfile
import unittest

from expense_tracker.reports import export_csv, export_table_pdf, shape_rtl
from expense_tracker.storage import ExpenseStore

tempfile.tempdir = str(Path(__file__).resolve().parents[1] / ".test-tmp")
Path(tempfile.tempdir).mkdir(exist_ok=True)


class ReportAndErrorSafetyTests(unittest.TestCase):
    def test_dari_text_is_shaped_for_chart_and_pdf_rendering(self):
        self.assertEqual(shape_rtl("AFN 10"), "AFN 10")
        self.assertNotEqual(shape_rtl("مصارف"), "مصارف")

    def test_invalid_inputs_are_actionable_and_do_not_create_records(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ExpenseStore(Path(directory) / "db.sqlite3")
            for values in [(1, "not-date", "", "Food"), (1, "2026-01-01", "", ""), ("NaN", "2026-01-01", "", "Food")]:
                with self.subTest(values=values), self.assertRaises(ValueError): store.add_expense(*values)
            self.assertEqual(store.count_expenses(), 0)

    def test_csv_neutralizes_spreadsheet_formulas_and_pdf_is_written(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ExpenseStore(Path(directory) / "db.sqlite3")
            store.add_expense(10, "2026-01-01", "=HYPERLINK(\"bad\")", "@category")
            csv_path = Path(directory) / "report.csv"
            self.assertEqual(export_csv(store, csv_path), 1)
            with csv_path.open(encoding="utf-8-sig") as file:
                rows = list(csv.reader(file))
            self.assertTrue(rows[1][3].startswith("'@"))
            self.assertTrue(rows[1][4].startswith("'="))
            pdf_path = export_table_pdf("Test", ["A", "B"], [["x", "y"]], Path(directory) / "report.pdf")
            self.assertTrue(pdf_path.read_bytes().startswith(b"%PDF"))


if __name__ == "__main__": unittest.main()
