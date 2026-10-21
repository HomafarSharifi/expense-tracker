from datetime import date
from decimal import Decimal
from pathlib import Path
import tempfile
import unittest

from expense_tracker.storage import ExpenseStore

tempfile.tempdir = str(Path(__file__).resolve().parents[1] / ".test-tmp")
Path(tempfile.tempdir).mkdir(exist_ok=True)


class ExpenseStorageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.store = ExpenseStore(Path(self.temporary.name) / "tracker.sqlite3")

    def tearDown(self):
        self.temporary.cleanup()

    def test_validates_amounts_and_dates_before_writing(self):
        for amount in (0, -1, "NaN", "1.001", "bad"):
            with self.subTest(amount=amount), self.assertRaises(ValueError):
                self.store.add_expense(amount, "2026-01-01", "", "Food")
        with self.assertRaises(ValueError):
            self.store.add_expense(1, "2026-02-30", "", "Food")
        self.assertEqual(self.store.count_expenses(), 0)

    def test_pagination_and_sort_modes_are_stable(self):
        for amount, day in ((5, "2026-01-01"), (20, "2026-01-03"), (10, "2026-01-02")):
            self.store.add_expense(amount, day, "", "Food")
        recent, total = self.store.page_expenses(1, 2, "recent")
        self.assertEqual([row["date"] for row in recent], ["2026-01-03", "2026-01-02"])
        self.assertEqual(total, 3)
        self.assertEqual(self.store.page_expenses(2, 2, "recent")[0][0]["date"], "2026-01-01")
        self.assertEqual(self.store.page_expenses(1, 2, "oldest")[0][0]["date"], "2026-01-01")
        self.assertEqual(self.store.page_expenses(1, 2, "highest")[0][0]["amount"], Decimal("20"))
        self.assertEqual(self.store.page_expenses(1, 2, "lowest")[0][0]["amount"], Decimal("5"))
        with self.assertRaises(ValueError): self.store.page_expenses(sort="amount DESC; DROP TABLE expenses" )

    def test_search_treats_sql_wildcards_as_literal_text(self):
        self.store.add_expense(1, "2026-01-01", "100% present", "Home")
        self.store.add_expense(1, "2026-01-01", "1000 present", "Home")
        self.assertEqual(self.store.page_expenses(search="100%")[1], 1)
        self.assertEqual(self.store.page_expenses(search="Home")[1], 2)

    def test_income_month_summary_and_preferences(self):
        self.store.add_expense("15.25", "2026-03-03", "Lunch", "Food")
        self.store.add_expense("4.75", "2026-03-04", "Bus", "Travel")
        self.store.add_income(50, "2026-03-01", "Salary")
        summary = self.store.summary("2026-03-01")
        self.assertEqual(summary["income"], Decimal("50"))
        self.assertEqual(summary["spending"], Decimal("20"))
        self.assertEqual(summary["remaining"], Decimal("30"))
        self.assertEqual(self.store.page_months()[0][0]["month"], "2026-03")
        self.assertEqual(self.store.page_income(search="sal")[1], 1)
        self.assertEqual(self.store.page_months(search="2026-03")[1], 1)
        self.store.set_preference("calendar", "Afghan Solar Hijri")
        self.assertEqual(self.store.get_preference("calendar"), "Afghan Solar Hijri")
        with self.assertRaises(ValueError): self.store.set_preference("password", "secret")

    def test_solar_month_summary_and_income_use_actual_calendar_boundaries(self):
        self.store.add_expense(10, "2024-03-20", "First day", "Home")
        self.store.add_expense(20, "2024-04-19", "Last day", "Home")
        self.store.add_expense(99, "2024-04-20", "Next month", "Home")
        self.store.add_income(100, "2024-03-20", "Salary")
        summary = self.store.summary("2024-03-20", period_start="2024-03-20", period_end="2024-04-19")
        self.assertEqual(summary["income"], Decimal("100"))
        self.assertEqual(summary["spending"], Decimal("30"))
        months, count = self.store.page_months(calendar="Afghan Solar Hijri")
        self.assertEqual(count, 2)
        self.assertEqual({item["month"] for item in months}, {"1403-01", "1403-02"})
        comparison = self.store.monthly_comparison("Afghan Solar Hijri")
        self.assertEqual(comparison[0]["month"], "1403-01")
        self.assertEqual(comparison[0]["income"], Decimal("100"))

    def test_income_uses_selected_calendar_month_date_boundaries(self):
        # A Gregorian month-start income belongs to the Solar Hijri month
        # containing that date too, so changing display calendars keeps it visible.
        self.store.add_income(42000, "2026-10-01", "Salary")
        solar_month = self.store.summary(
            "2026-09-23", period_start="2026-09-23", period_end="2026-10-22"
        )
        next_month = self.store.summary(
            "2026-10-23", period_start="2026-10-23", period_end="2026-11-21"
        )
        self.assertEqual(solar_month["income"], Decimal("42000"))
        self.assertEqual(next_month["income"], Decimal("0"))

    def test_update_delete_and_missing_record(self):
        record_id = self.store.add_expense(10, date(2026, 1, 1), "", "Food")
        self.store.update_expense(record_id, 11, "2026-01-02", "Bread", "Groceries")
        self.assertEqual(self.store.get_expense(record_id)["amount"], Decimal("11"))
        self.store.delete_expense(record_id)
        self.assertIsNone(self.store.get_expense(record_id))
        with self.assertRaises(LookupError): self.store.delete_expense(record_id)


if __name__ == "__main__": unittest.main()
