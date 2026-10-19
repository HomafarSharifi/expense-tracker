"""Afghan Solar Hijri calendar helpers; database dates remain Gregorian."""

from datetime import date, datetime, timedelta


AFGHAN_MONTHS = (
    "حمل", "ثور", "جوزا", "سرطان", "اسد", "سنبله",
    "میزان", "عقرب", "قوس", "جدی", "دلو", "حوت",
)


def as_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()


def to_jalali(value):
    """Convert a Gregorian date using the Solar Hijri 33-year cycle."""
    current = as_date(value)
    gy, gm, gd = current.year - 1600, current.month - 1, current.day - 1
    gregorian_month_days = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    day_number = 365 * gy + (gy + 3) // 4 - (gy + 99) // 100 + (gy + 399) // 400
    for month in range(gm):
        day_number += gregorian_month_days[month]
    if gm > 1 and (current.year % 4 == 0 and (current.year % 100 != 0 or current.year % 400 == 0)):
        day_number += 1
    day_number += gd

    jalali_day_number = day_number - 79
    cycles, jalali_day_number = divmod(jalali_day_number, 12053)
    year = 979 + 33 * cycles + 4 * (jalali_day_number // 1461)
    jalali_day_number %= 1461
    if jalali_day_number >= 366:
        year += (jalali_day_number - 1) // 365
        jalali_day_number = (jalali_day_number - 1) % 365
    if jalali_day_number < 186:
        month = 1 + jalali_day_number // 31
        day = 1 + jalali_day_number % 31
    else:
        month = 7 + (jalali_day_number - 186) // 30
        day = 1 + (jalali_day_number - 186) % 30
    return JalaliDate(year, month, day)


def to_gregorian(year, month, day):
    year, month, day = int(year), int(month), int(day)
    if month < 1 or month > 12 or day < 1 or day > jalali_month_days(year, month):
        raise ValueError("Invalid Afghan Solar Hijri date")
    jalali_year = year - 979
    jalali_day_number = (
        365 * jalali_year
        + (jalali_year // 33) * 8
        + ((jalali_year % 33 + 3) // 4)
        + day - 1
    )
    if month <= 6:
        jalali_day_number += (month - 1) * 31
    else:
        jalali_day_number += 186 + (month - 7) * 30

    gregorian_day_number = jalali_day_number + 79
    gy = 1600 + 400 * (gregorian_day_number // 146097)
    gregorian_day_number %= 146097
    leap = True
    if gregorian_day_number >= 36525:
        gregorian_day_number -= 1
        gy += 100 * (gregorian_day_number // 36524)
        gregorian_day_number %= 36524
        if gregorian_day_number >= 365:
            gregorian_day_number += 1
        else:
            leap = False
    gy += 4 * (gregorian_day_number // 1461)
    gregorian_day_number %= 1461
    if gregorian_day_number >= 366:
        leap = False
        gy += (gregorian_day_number - 1) // 365
        gregorian_day_number = (gregorian_day_number - 1) % 365
    gregorian_month_days = (31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    month_index = 0
    while gregorian_day_number >= gregorian_month_days[month_index]:
        gregorian_day_number -= gregorian_month_days[month_index]
        month_index += 1
    return date(gy, month_index + 1, gregorian_day_number + 1)


def jalali_month_start(value):
    jalali = to_jalali(value)
    return to_gregorian(jalali.year, jalali.month, 1)


def jalali_month_bounds(value):
    jalali = to_jalali(value)
    start = to_gregorian(jalali.year, jalali.month, 1)
    if jalali.month == 12:
        next_start = to_gregorian(jalali.year + 1, 1, 1)
    else:
        next_start = to_gregorian(jalali.year, jalali.month + 1, 1)
    return start, date.fromordinal(next_start.toordinal() - 1)


def month_key(value):
    jalali = to_jalali(value)
    return f"{jalali.year:04d}-{jalali.month:02d}"


def format_jalali_date(value):
    jalali = to_jalali(value)
    return f"{jalali.day:02d} {AFGHAN_MONTHS[jalali.month - 1]} {jalali.year}"


def format_jalali_month(value):
    jalali = to_jalali(value)
    return f"{AFGHAN_MONTHS[jalali.month - 1]} {jalali.year}"


def jalali_month_days(year, month):
    if month <= 6:
        return 31
    if month <= 11:
        return 30
    year = int(year)
    return 30 if _jalali_year_day_number(year + 1) - _jalali_year_day_number(year) == 366 else 29


def _jalali_year_day_number(year):
    year -= 979
    return 365 * year + (year // 33) * 8 + ((year % 33 + 3) // 4)


class JalaliDate:
    """Small immutable-style date result compatible with the fields used by the UI."""

    __slots__ = ("year", "month", "day")

    def __init__(self, year, month, day):
        self.year = year
        self.month = month
        self.day = day

    def __repr__(self):
        return f"JalaliDate({self.year}, {self.month}, {self.day})"

    def __str__(self):
        return f"{self.year:04d}-{self.month:02d}-{self.day:02d}"

