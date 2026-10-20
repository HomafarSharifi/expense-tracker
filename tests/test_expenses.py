from decimal import Decimal
from unittest import TestCase
from unittest.mock import Mock, patch

import expenses
from database_errors import database_error_help


class ExpenseValidationTests(TestCase):
    def test_rejects_invalid_expenses(self):
        values = [
            (0, "2026-01-01", "", "Food"),
            (-1, "2026-01-01", "", "Food"),
            ("NaN", "2026-01-01", "", "Food"),
            ("100000000", "2026-01-01", "", "Food"),
            ("1.001", "2026-01-01", "", "Food"),
            (1, "2026-02-30", "", "Food"),
            (1, "2026-01-01", "", " "),
            (1, "2026-01-01", "", "x" * 41),
            (1, "2026-01-01", "x" * 101, "Food"),
        ]
        for expense in values:
            with self.subTest(expense=expense):
                self.assertFalse(expenses.validate_expense(*expense))

    def test_accepts_valid_expense(self):
        self.assertTrue(
            expenses.validate_expense(
                Decimal("12.50"), "2026-01-31", None, " Food "
            )
        )

    def test_validates_date_ranges(self):
        cases = [
            ("2026-01-01", "2026-01-31", True),
            ("2026-01-31", "2026-01-01", False),
            ("2026-02-30", "2026-03-01", False),
            ("bad", "2026-03-01", False),
        ]
        for start, end, expected in cases:
            with self.subTest(start=start, end=end):
                self.assertEqual(
                    expenses.validate_date_range(start, end), expected
                )

    def test_validates_monthly_income(self):
        self.assertTrue(expenses.validate_income("2500.00", "2026-01", "Salary"))
        for amount, month, source in [
            (0, "2026-01", "Salary"),
            ("NaN", "2026-01", "Salary"),
            ("1.001", "2026-01", "Salary"),
            (1, "2026-13", "Salary"),
            (1, "2026-01", " "),
            (1, "2026-01", "x" * 81),
        ]:
            with self.subTest(amount=amount, month=month, source=source):
                self.assertFalse(expenses.validate_income(amount, month, source))

    def test_monthly_income_normalizes_date_to_month_start(self):
        self.assertTrue(expenses.validate_income(1, "2026-01-31", "Salary"))
        self.assertFalse(expenses.validate_income(1, "2026-02-30", "Salary"))


class DatabaseErrorGuidanceTests(TestCase):
    def test_identifies_missing_income_table(self):
        error = RuntimeError("table missing")
        error.errno = 1146
        error.msg = "Table 'expense_tracker.monthly_income' doesn't exist"
        message, diagnostic = database_error_help(error)
        self.assertIn("monthly_income", message)
        self.assertIn("Run income.sql", message)
        self.assertIn("expense_tracker.monthly_income", diagnostic)

    def test_identifies_missing_expenses_table(self):
        error = RuntimeError("table missing")
        error.errno = 1146
        error.msg = "Table 'expense_tracker.expenses' doesn't exist"
        message, _ = database_error_help(error)
        self.assertIn("Import expenses.sql", message)

    def test_gives_connection_guidance(self):
        error = RuntimeError("connection unavailable")
        error.errno = 2003
        error.msg = "Can't connect"
        message, _ = database_error_help(error)
        self.assertIn("Start MySQL/MariaDB", message)


class DatabaseOperationTests(TestCase):
    def test_invalid_date_range_does_not_open_database(self):
        with patch.object(expenses, "get_connection") as connect:
            self.assertEqual(
                expenses.get_spending_by_date_range(
                    "2026-02-01", "2026-01-01"
                ),
                [],
            )
        connect.assert_not_called()

    def test_add_commits_and_closes_resources(self):
        cursor = Mock()
        connection = Mock()
        connection.cursor.return_value = cursor
        with patch.object(expenses, "get_connection", return_value=connection):
            self.assertTrue(
                expenses.add_expense(12, "2026-01-01", "", " Food ")
            )
        connection.commit.assert_called_once()
        cursor.close.assert_called_once()
        connection.close.assert_called_once()
        self.assertEqual(
            cursor.execute.call_args.args[1],
            (12, "2026-01-01", None, "Food"),
        )

    def test_add_failure_rolls_back_and_closes_resources(self):
        cursor = Mock()
        cursor.execute.side_effect = RuntimeError("database unavailable")
        connection = Mock()
        connection.cursor.return_value = cursor
        with self.assertLogs("expenses", level="ERROR") as captured:
            with patch.object(expenses, "get_connection", return_value=connection):
                self.assertFalse(
                    expenses.add_expense(12, "2026-01-01", "", "Food")
                )
        self.assertIn("RuntimeError", captured.output[0])
        connection.rollback.assert_called_once()
        cursor.close.assert_called_once()
        connection.close.assert_called_once()

    def test_delete_missing_expense_does_not_commit(self):
        cursor = Mock(rowcount=0)
        connection = Mock()
        connection.cursor.return_value = cursor
        with patch.object(expenses, "get_connection", return_value=connection):
            self.assertFalse(expenses.delete_expense(1))
        connection.commit.assert_not_called()

    def test_unchanged_update_of_existing_expense_succeeds(self):
        cursor = Mock(rowcount=0)
        cursor.fetchone.return_value = (1,)
        connection = Mock()
        connection.cursor.return_value = cursor
        with patch.object(expenses, "get_connection", return_value=connection):
            self.assertTrue(
                expenses.update_expense(
                    1, 12, "2026-01-01", "", "Food"
                )
            )
        connection.commit.assert_called_once()

    def test_add_income_commits_with_normalized_month_and_source(self):
        cursor = Mock()
        connection = Mock()
        connection.cursor.return_value = cursor
        with patch.object(expenses, "get_connection", return_value=connection):
            self.assertTrue(expenses.add_monthly_income(2500, "2026-01-15", " Salary "))
        connection.commit.assert_called_once()
        self.assertEqual(cursor.execute.call_args.args[1], (expenses.date(2026, 1, 1), "Salary", 2500))
        cursor.close.assert_called_once()
        connection.close.assert_called_once()

    def test_add_income_can_preserve_solar_month_start(self):
        cursor = Mock()
        connection = Mock()
        connection.cursor.return_value = cursor
        solar_month_start = expenses.date(2024, 3, 20)
        with patch.object(expenses, "get_connection", return_value=connection):
            self.assertTrue(
                expenses.add_monthly_income(
                    2500, solar_month_start, "Salary", exact=True
                )
            )
        self.assertEqual(
            cursor.execute.call_args.args[1], (solar_month_start, "Salary", 2500)
        )
        connection.commit.assert_called_once()

    def test_invalid_income_does_not_open_database(self):
        with patch.object(expenses, "get_connection") as connect:
            self.assertFalse(expenses.add_monthly_income(0, "2026-01", "Salary"))
        connect.assert_not_called()

    def test_income_total_uses_month_first_day(self):
        with patch.object(expenses, "_fetch_one", return_value=(Decimal("2500.00"),)) as fetch:
            self.assertEqual(expenses.get_monthly_income_total("2026-01-31"), Decimal("2500.00"))
        self.assertEqual(fetch.call_args.args[1], (expenses.date(2026, 1, 1),))

    def test_income_total_can_query_solar_month_date_range(self):
        start, end = expenses.date(2024, 3, 20), expenses.date(2024, 4, 19)
        with patch.object(expenses, "_fetch_one", return_value=(Decimal("2500.00"),)) as fetch:
            self.assertEqual(
                expenses.get_monthly_income_total(start, exact=True, period_end=end),
                Decimal("2500.00"),
            )
        self.assertEqual(fetch.call_args.args[1], (start, end))
