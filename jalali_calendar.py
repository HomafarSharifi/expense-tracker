"""Afghan Solar Hijri calendar helpers; database dates remain Gregorian."""

from datetime import date, datetime

import jdatetime


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
    return jdatetime.date.fromgregorian(date=as_date(value))


def to_gregorian(year, month, day):
    return jdatetime.date(int(year), int(month), int(day)).togregorian()


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
    return 30 if jdatetime.date(int(year), 12, 1).isleap() else 29

