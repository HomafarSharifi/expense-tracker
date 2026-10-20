import unittest
from datetime import date

from jalali_calendar import (
    AFGHAN_MONTHS,
    calendar_date_to_gregorian,
    format_jalali_date,
    jalali_month_bounds,
    jalali_month_days,
    month_key,
    to_gregorian,
    to_jalali,
)


class AfghanJalaliCalendarTests(unittest.TestCase):
    def test_afghan_new_year_round_trips(self):
        self.assertEqual(str(to_jalali(date(2024, 3, 20))), "1403-01-01")
        self.assertEqual(to_gregorian(1403, 1, 1), date(2024, 3, 20))

    def test_afghan_month_names_are_used(self):
        self.assertEqual(AFGHAN_MONTHS[0], "حمل")
        self.assertEqual(AFGHAN_MONTHS[-1], "حوت")
        self.assertEqual(format_jalali_date(date(2024, 3, 20)), "01 حمل 1403")

    def test_month_boundaries_follow_the_solar_calendar(self):
        start, end = jalali_month_bounds(date(2024, 4, 1))
        self.assertEqual((start, end), (date(2024, 3, 20), date(2024, 4, 19)))
        self.assertEqual(month_key(date(2024, 4, 1)), "1403-01")

    def test_leap_year_has_thirty_days_in_hut(self):
        self.assertEqual(jalali_month_days(1403, 12), 30)
        self.assertEqual(jalali_month_days(1404, 12), 29)

    def test_calendar_selector_accepts_serialized_widget_values(self):
        self.assertEqual(
            calendar_date_to_gregorian("2024", "3", "20", "Gregorian"),
            date(2024, 3, 20),
        )
        self.assertEqual(
            calendar_date_to_gregorian("1403", "1", "1", "Afghan Solar Hijri"),
            date(2024, 3, 20),
        )

    def test_calendar_selector_rejects_unknown_or_invalid_dates(self):
        with self.assertRaises(ValueError):
            calendar_date_to_gregorian("2024", "2", "30", "Gregorian")
        with self.assertRaises(ValueError):
            calendar_date_to_gregorian("1403", "13", "1", "Afghan Solar Hijri")
        with self.assertRaises(ValueError):
            calendar_date_to_gregorian("2024", "1", "1", "Other")


if __name__ == "__main__":
    unittest.main()
