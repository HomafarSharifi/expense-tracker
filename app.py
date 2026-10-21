import base64
import html
import os
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pandas as pd
import streamlit as st

from database_errors import database_error_help
from data_backup import backup_database
from jalali_calendar import (
    AFGHAN_MONTHS,
    calendar_date_to_gregorian,
    format_jalali_date,
    format_jalali_month,
    jalali_month_bounds,
    jalali_month_days,
    month_key as jalali_month_key,
    to_jalali,
)
from expenses import (
    add_expense,
    add_monthly_income,
    delete_expense,
    delete_monthly_income,
    get_expenses,
    get_income_and_spending_by_month,
    get_monthly_income_entries,
    get_monthly_income_total,
    get_spending_by_date_range,
    update_expense,
    validate_expense,
    validate_income,
)

CURRENCY = os.getenv("EXPENSE_CURRENCY", "AFN").upper()
LOGO_PATH = Path(__file__).resolve().parent / "assets" / "expense-tracker-logo.svg"
NEW_CATEGORY = "Create a new category..."
LANGUAGE_OPTIONS = ["English", "دری"]
CATEGORY_TRANSLATIONS = {
    "FOOD": "غذا",
    "TRANSPORT": "ترانسپورت",
    "EDUCATION": "آموزش",
    "ENTERTAINMENT": "سرگرمی",
    "HEALTH": "صحت",
    "UTILITIES": "خدمات عمومی",
    "HOUSING": "مسکن",
    "SHOPPING": "خرید",
    "OTHER": "سایر",
}
TRANSLATIONS = {
    "Personal Expense Tracker": "مدیریت مصارف شخصی",
    "Expense Tracker": "مدیریت مصارف",
    "A clear view of where your money goes.": "نمای روشن از این‌که پول شما در کجا مصرف می‌شود.",
    "Quick add": "ثبت سریع",
    "Capture an expense without leaving your current view.": "بدون ترک صفحهٔ فعلی، مصرف خود را ثبت کنید.",
    "Amount": "مقدار",
    "Date": "تاریخ",
    "Year": "سال",
    "Month": "ماه",
    "Day": "روز",
    "Category": "دسته‌بندی",
    "New category (when creating one)": "دسته‌بندی جدید (برای ساختن دسته‌بندی)",
    "What was it for?": "این مصرف برای چه بود؟",
    "e.g. Lunch": "مثلاً ناهار",
    "Save expense": "ثبت مصرف",
    "Expense saved.": "مصرف ثبت شد.",
    "Could not save the expense. Check your database connection and try again.": "مصرف ثبت نشد. اتصال پایگاه داده را بررسی و دوباره تلاش کنید.",
    "Check the amount, date, category (1–40 characters), and reason (up to 100 characters).": "مقدار، تاریخ، دسته‌بندی (۱ تا ۴۰ نویسه) و توضیح (حداکثر ۱۰۰ نویسه) را بررسی کنید.",
    "Language": "زبان",
    "Calendar": "تقویم",
    "Gregorian": "میلادی",
    "Afghan Solar Hijri": "هجری خورشیدی افغانستان",
    "Current system date and time: {date} · {time}": "تاریخ و زمان سیستم: {date} · {time}",
    "System time: {date} · {time}": "زمان سیستم: {date} · {time}",
    "The app uses the system clock of the computer running it. Turn on automatic time synchronization in system settings to keep it aligned with internet time.": "برنامه از ساعت سیستم کمپیوتر اجراکنندهٔ خود استفاده می‌کند. برای هماهنگی با زمان اینترنت، همگام‌سازی خودکار ساعت را در تنظیمات سیستم روشن کنید.",
    "January": "جنوری", "February": "فبروری", "March": "مارچ", "April": "اپریل",
    "May": "می", "June": "جون", "July": "جولای", "August": "اگست",
    "September": "سپتمبر", "October": "اکتوبر", "November": "نومبر", "December": "دسمبر",
    "Advanced settings": "تنظیمات پیشرفته",
    "Display and database settings": "تنظیمات نمایش و پایگاه داده",
    "Current currency": "واحد پول فعلی",
    "Database connection": "اتصال پایگاه داده",
    "Connected": "متصل است",
    "Not connected": "وصل نیست",
    "Retry database connection": "دوباره اتصال به پایگاه داده",
    "Host": "میزبان",
    "Port": "درگاه",
    "Database": "پایگاه داده",
    "Account": "حساب کاربری",
    "The password is hidden. Edit .streamlit/secrets.toml to change connection settings.": "گذرواژه پنهان است. برای تغییر تنظیمات اتصال، فایل .streamlit/secrets.toml را ویرایش کنید.",
    "Database settings are read from environment variables first, then from .streamlit/secrets.toml.": "تنظیمات پایگاه داده ابتدا از متغیرهای محیطی و سپس از فایل .streamlit/secrets.toml خوانده می‌شوند.",
    "Currency display can be changed with EXPENSE_CURRENCY in the system environment.": "واحد پول نمایشی را می‌توانید با EXPENSE_CURRENCY در متغیرهای محیطی سیستم تغییر دهید.",
    "Local data backup": "نسخهٔ پشتیبان محلی",
    "A backup contains private financial records and is not encrypted. Keep it in a secure location.": "نسخهٔ پشتیبان شامل اطلاعات مالی خصوصی و رمزگذاری‌نشده است. آن را در جای امن نگهداری کنید.",
    "Create backup": "ساخت نسخهٔ پشتیبان",
    "Download backup": "بارگیری نسخهٔ پشتیبان",
    "Backup created: {filename}": "نسخهٔ پشتیبان ساخته شد: {filename}",
    "Backup failed. Check the database connection and try again.": "ساخت نسخهٔ پشتیبان انجام نشد. اتصال پایگاه داده را بررسی و دوباره تلاش کنید.",
    "Configuration help": "راهنمای تنظیمات",
    "Diagnostic": "تشخیص",
    "Could not connect to the configured MySQL server. Start MySQL/MariaDB and verify EXPENSE_DB_HOST and EXPENSE_DB_PORT.": "اتصال به سرور MySQL ممکن نشد. MySQL/MariaDB را روشن کرده و EXPENSE_DB_HOST و EXPENSE_DB_PORT را بررسی کنید.",
    "MySQL rejected the login. Verify EXPENSE_DB_USER and EXPENSE_DB_PASSWORD.": "ورود به MySQL رد شد. EXPENSE_DB_USER و EXPENSE_DB_PASSWORD را بررسی کنید.",
    "The configured database does not exist. Create expense_tracker or set EXPENSE_DB_NAME to the correct database.": "پایگاه دادهٔ تنظیم‌شده وجود ندارد. expense_tracker را بسازید یا EXPENSE_DB_NAME را درست تنظیم کنید.",
    "The database account lacks permission for this database. Ask the database administrator to grant the app account access to expense_tracker.": "حساب پایگاه داده اجازهٔ دسترسی به این پایگاه داده را ندارد. از مدیر پایگاه داده بخواهید دسترسی حساب برنامه را به expense_tracker بدهد.",
    "A database setting is invalid. Check that the database port and connection timeout are whole numbers.": "یکی از تنظیمات پایگاه داده نادرست است. بررسی کنید شمارهٔ درگاه و مهلت اتصال عدد صحیح باشند.",
    "The app could not complete the database request. Refresh and try again; if it continues, review the database diagnostic.": "برنامه نتوانست درخواست پایگاه داده را تکمیل کند. صفحه را تازه و دوباره تلاش کنید؛ اگر مشکل ادامه داشت، پیام تشخیصی را بررسی کنید.",
    "The database schema does not match this app version. Review the SQL setup instructions in README.md before changing any tables.": "ساختار پایگاه داده با نسخهٔ برنامه مطابقت ندارد. پیش از تغییر جدول‌ها، راهنمای نصب SQL در README.md را بررسی کنید.",
    "The database was busy and cancelled this request. Refresh and try again.": "پایگاه داده مشغول بود و درخواست را لغو کرد. صفحه را تازه و دوباره تلاش کنید.",
    "The connection to MySQL was interrupted. Check that the database server is running, then refresh and try again.": "اتصال به MySQL قطع شد. روشن بودن سرور پایگاه داده را بررسی کنید و سپس صفحه را تازه کنید.",
    "The monthly_income table is missing from the database the app connected to. Run income.sql against that same database.": "جدول monthly_income در پایگاه دادهٔ متصل‌شده وجود ندارد. فایل income.sql را روی همان پایگاه داده اجرا کنید.",
    "The expenses table is missing from the database the app connected to. Import expenses.sql, then run income.sql.": "جدول expenses در پایگاه دادهٔ متصل‌شده وجود ندارد. ابتدا expenses.sql و سپس income.sql را وارد کنید.",
    "The app could not read its data. Check the technical details below.": "برنامه نتوانست داده‌ها را بخواند. جزئیات فنی زیر را بررسی کنید.",
    "Change it with the EXPENSE_CURRENCY environment variable.": "واحد پول را با متغیر محیطی EXPENSE_CURRENCY تغییر دهید.",
    "Currency display: {currency}": "واحد پول نمایشی: {currency}",
    "Overview": "نمای کلی",
    "Analytics": "تحلیل‌ها",
    "Income": "درآمد",
    "Monthly income": "درآمد ماهانه",
    "Month": "ماه",
    "Spending": "مصارف",
    "Daily spending": "مصارف روزانه",
    "Manage expenses": "مدیریت مصارف",
    "Monthly money at a glance": "خلاصهٔ وضعیت پول در ماه",
    "Choose a month": "یک ماه را انتخاب کنید",
    "Choose a month to see that month's income and spending.": "ماه را انتخاب کنید تا درآمد و مصارف همان ماه را ببینید.",
    "Income this month": "درآمد این ماه",
    "Spent this month": "مصرف‌شده در این ماه",
    "Money remaining": "پول باقی‌مانده",
    "Within income": "در محدودهٔ درآمد",
    "Over income": "بیشتر از درآمد",
    "Add salary or another income in the Income tab to see your monthly balance.": "برای دیدن توازن ماهانه، معاش یا درآمد دیگری را در بخش «درآمد» ثبت کنید.",
    "Your spending is higher than the income recorded for this month.": "مصارف شما از درآمد ثبت‌شدهٔ این ماه بیشتر است.",
    "All-time spending: {amount} · {expenses} expenses · {categories} categories": "مجموع مصارف: {amount} · {expenses} مصرف · {categories} دسته‌بندی",
    "Expense history": "تاریخچهٔ مصارف",
    "Find expenses": "پیدا کردن مصرف",
    "Choose a category or search descriptions to narrow this list.": "برای محدود کردن فهرست، دسته‌بندی را انتخاب کنید یا توضیحات را جست‌وجو کنید.",
    "Clear filters": "پاک کردن فیلترها",
    "Filter by category": "فیلتر بر اساس دسته‌بندی",
    "All categories": "همهٔ دسته‌بندی‌ها",
    "Search expenses": "جست‌وجوی مصارف",
    "Search descriptions or categories": "جست‌وجوی توضیحات یا دسته‌بندی‌ها",
    "Reason": "توضیحات",
    "Showing {visible} of {total} expenses.": "نمایش {visible} از {total} مصرف.",
    "No expenses match those filters. Clear the search or choose another category.": "هیچ مصرفی با این فیلترها پیدا نشد. جست‌وجو را پاک کنید یا دسته‌بندی دیگری برگزینید.",
    "No expenses yet. Add your first one from Quick add.": "هنوز مصرفی ثبت نشده است. نخستین مورد را از بخش ثبت سریع اضافه کنید.",
    "You can also use the Manage expenses tab for a detailed entry.": "همچنان می‌توانید برای ثبت جزئیات بیشتر از بخش مدیریت مصارف استفاده کنید.",
    "Spending patterns": "الگوهای مصرف",
    "Spending by category": "مصارف بر اساس دسته‌بندی",
    "Total spending": "مجموع مصارف",
    "Category insights will appear after you record an expense.": "پس از ثبت مصرف، تحلیل دسته‌بندی‌ها نمایش داده می‌شود.",
    "Monthly spending": "مصارف ماهانه",
    "Monthly chart": "نمودار ماهانه",
    "Choose a monthly view to see totals, category details, or compare income with spending.": "یکی از نمودارهای ماهانه را انتخاب کنید تا مجموع، دسته‌بندی‌ها یا مقایسهٔ درآمد و مصارف را ببینید.",
    "Total spending by category, with a distinct color for each category.": "مجموع مصارف هر دسته‌بندی با رنگ جداگانه.",
    "Monthly spending stacked by category.": "مصارف ماهانه به تفکیک دسته‌بندی.",
    "Total spending for each month in chronological order.": "مجموع مصارف هر ماه به ترتیب زمانی.",
    "Income vs spending": "درآمد در برابر مصارف",
    "Monthly income and spending compared in chronological order.": "مقایسهٔ درآمد و مصارف ماهانه به ترتیب زمانی.",
    "No spending recorded yet. Add expenses to see monthly totals.": "هنوز مصرفی ثبت نشده است. برای دیدن مجموع ماهانه، مصرف اضافه کنید.",
    "No spending recorded yet. Add expenses to see category totals by month.": "هنوز مصرفی ثبت نشده است. برای دیدن دسته‌بندی‌های ماهانه، مصرف اضافه کنید.",
    "Monthly trends will appear after you record income or an expense.": "پس از ثبت درآمد یا مصرف، روند ماهانه نمایش داده می‌شود.",
    "Add income or expenses to compare monthly cash flow.": "برای مقایسهٔ جریان پول ماهانه، درآمد یا مصرف ثبت کنید.",
    "Explore a date range": "بررسی یک بازهٔ زمانی",
    "From": "از تاریخ",
    "Through": "تا تاریخ",
    "The start date must be on or before the end date.": "تاریخ آغاز باید قبل یا برابر با تاریخ پایان باشد.",
    "Spending in this period": "مصارف در این بازه",
    "Expenses in this period": "تعداد مصارف در این بازه",
    "View expenses in this period": "دیدن مصارف این بازه",
    "No expenses were recorded in this date range.": "در این بازهٔ زمانی مصرفی ثبت نشده است.",
    "Daily trend": "روند روزانه",
    "Daily spending over the selected date range.": "مصارف روزانه در بازهٔ انتخاب‌شده.",
    "Record each income source for a month. Multiple entries are added together in your balance.": "هر منبع درآمد را برای یک ماه ثبت کنید. مجموع چند مورد در توازن شما حساب می‌شود.",
    "Income month": "ماه درآمد",
    "Source": "منبع",
    "e.g. Salary, freelance work": "مثلاً معاش یا کار آزاد",
    "Add income": "ثبت درآمد",
    "Enter a positive amount and an income source of 1–80 characters.": "مقداری مثبت و منبع درآمدی با ۱ تا ۸۰ نویسه وارد کنید.",
    "Income added successfully.": "درآمد با موفقیت ثبت شد.",
    "Could not save income. Check the database connection and confirm income.sql has been applied.": "درآمد ثبت نشد. اتصال پایگاه داده و اجرای فایل income.sql را بررسی کنید.",
    "Total income · {month}": "مجموع درآمد · {month}",
    "Remove an income entry": "حذف یک مورد درآمد",
    "I understand this permanently deletes the selected income.": "می‌دانم که این مورد درآمد برای همیشه حذف می‌شود.",
    "I understand this permanently deletes the selected expense.": "می‌دانم که این مصرف برای همیشه حذف می‌شود.",
    "Delete income": "حذف درآمد",
    "Income entry deleted.": "مورد درآمد حذف شد.",
    "Could not delete income. Refresh and try again.": "درآمد حذف نشد. صفحه را تازه‌سازی و دوباره تلاش کنید.",
    "No income recorded for this month. Add salary or another source above.": "برای این ماه درآمدی ثبت نشده است. معاش یا منبع دیگری را در بالا اضافه کنید.",
    "Add expense": "ثبت مصرف",
    "Update expense": "ویرایش مصرف",
    "Delete expense": "حذف مصرف",
    "Add a detailed expense": "ثبت مصرف با جزئیات",
    "Manage your expenses here. Add a new record, update an existing one, or delete it after confirmation.": "مصارف خود را در این‌جا مدیریت کنید: مورد تازه ثبت کنید، مورد قبلی را ویرایش کنید یا پس از تأیید حذف نمایید.",
    "Choose a category. The extra field appears only when you create a new category.": "دسته‌بندی را انتخاب کنید. خانهٔ اضافی فقط هنگام ساختن دسته‌بندی جدید نمایش داده می‌شود.",
    "Income is for the selected month. Add each source separately; the app adds them together.": "درآمد برای ماه انتخاب‌شده است. هر منبع را جداگانه ثبت کنید؛ برنامه آن‌ها را باهم جمع می‌کند.",
    "e.g. Groceries": "مثلاً خرید مواد غذایی",
    "Create a new category...": "ساختن دسته‌بندی جدید...",
    "Save changes": "ذخیرهٔ تغییرات",
    "Expense added successfully.": "مصرف با موفقیت ثبت شد.",
    "Could not save the expense. Check your database connection.": "مصرف ثبت نشد. اتصال پایگاه داده را بررسی کنید.",
    "Add an expense first; it will appear here for editing.": "برای ویرایش، ابتدا یک مصرف ثبت کنید.",
    "Choose an expense": "یک مصرف را انتخاب کنید",
    "No description": "بدون توضیح",
    "Could not update the expense. Refresh and try again.": "مصرف ویرایش نشد. صفحه را تازه‌سازی و دوباره تلاش کنید.",
    "Expense updated successfully.": "مصرف با موفقیت ویرایش شد.",
    "There are no expenses to delete.": "مصرفی برای حذف وجود ندارد.",
    "Expense deleted.": "مصرف حذف شد.",
    "Could not delete the expense. Refresh and try again.": "مصرف حذف نشد. صفحه را تازه‌سازی و دوباره تلاش کنید.",
    "A required table is missing. Check that your SQL file was run against the same database named by EXPENSE_DB_NAME.": "یک جدول ضروری وجود ندارد. بررسی کنید فایل SQL را روی همان پایگاه دادهٔ EXPENSE_DB_NAME اجرا کرده باشید.",
}


def t(text):
    """Translate a UI string to Dari; values and user-entered categories stay untouched."""
    if st.session_state.get("language", "English") == "دری":
        return TRANSLATIONS.get(text, text)
    return text


def language_widget_key(name):
    """Give language-sensitive widgets keys that refresh their visible translated label."""
    suffix = "dari" if st.session_state.get("language", "English") == "دری" else "english"
    return f"{name}_{suffix}"


def sync_language_widget_state():
    """Carry a widget's raw choice across language changes while refreshing its label."""
    current_language = st.session_state.get("language", "English")
    previous_language = st.session_state.get("_widget_language", current_language)
    if current_language == previous_language:
        st.session_state["_widget_language"] = current_language
        return

    previous_suffix = "dari" if previous_language == "دری" else "english"
    current_suffix = "dari" if current_language == "دری" else "english"
    for name in (
        "quick_category",
        "history_category",
        "monthly_chart_view",
        "add_category_choice",
        "update_category_choice",
    ):
        previous_key = f"{name}_{previous_suffix}"
        current_key = f"{name}_{current_suffix}"
        if previous_key in st.session_state:
            previous_value = st.session_state[previous_key]
            if name == "monthly_chart_view":
                st.session_state[current_key] = t(source_option(previous_value))
            else:
                st.session_state[current_key] = category_option_label(
                    category_option_value(previous_value)
                )
    # Month names are formatted by the active language, so use fresh widget IDs
    # and carry their numeric selection over when the language changes.
    for name in (
        "quick_date", "overview_month", "filter_start_date", "filter_end_date",
        "income_month", "add_date", "update_date",
    ):
        previous_key = f"{name}_month_{previous_suffix}"
        current_key = f"{name}_month_{current_suffix}"
        if previous_key in st.session_state:
            st.session_state[current_key] = st.session_state[previous_key]
    st.session_state["_widget_language"] = current_language


def category_label(value):
    """Translate familiar category names for display without changing stored values."""
    if st.session_state.get("language", "English") == "دری":
        return CATEGORY_TRANSLATIONS.get(str(value).strip().upper(), value)
    return value


def category_option_label(value):
    if value in (NEW_CATEGORY, "All categories"):
        return t(value)
    return category_label(value)


def category_option_value(label):
    """Convert a displayed category choice back to its stable database value."""
    if label in (NEW_CATEGORY, TRANSLATIONS[NEW_CATEGORY]):
        return NEW_CATEGORY
    if label in ("All categories", TRANSLATIONS["All categories"]):
        return "All categories"
    translated_to_source = {
        translated: source for source, translated in CATEGORY_TRANSLATIONS.items()
    }
    return translated_to_source.get(label, label)


def category_widget_key(name, values):
    """Keep the stored selection valid after translating or removing a category."""
    key = language_widget_key(name)
    available_labels = [category_option_label(value) for value in values]
    if key in st.session_state:
        selected_value = category_option_value(st.session_state[key])
        selected_label = category_option_label(selected_value)
        st.session_state[key] = (
            selected_label if selected_label in available_labels else available_labels[0]
        )
    return key


def source_option(label):
    """Recover a translated chart choice's stable English key."""
    return next(
        (source for source, translated in TRANSLATIONS.items() if translated == label),
        label,
    )


def sync_calendar_widget_state():
    """Keep currently selected dates when changing the calendar selector."""
    old_calendar = st.session_state.get(
        "_previous_calendar_type", "Gregorian"
    )
    new_calendar = st.session_state.get("calendar_type", "Gregorian")
    if old_calendar == new_calendar:
        return
    for key, month_only in (
        ("quick_date", False), ("overview_month", True), ("filter_start_date", False),
        ("filter_end_date", False), ("income_month", True), ("add_date", False),
        ("update_date", False),
    ):
        if old_calendar == "Gregorian":
            year = st.session_state.get(f"{key}_year")
            month = st.session_state.get(language_widget_key(f"{key}_month"))
            day = st.session_state.get(f"{key}_day")
            try:
                selected = calendar_date_to_gregorian(
                    year, month, 1 if month_only else day, "Gregorian"
                )
            except (TypeError, ValueError, OverflowError):
                # Repair stale/serialized widget values instead of crashing on a rerun.
                selected = st.session_state.get(
                    key, datetime.now().astimezone().date()
                )
                if not isinstance(selected, date):
                    selected = datetime.now().astimezone().date()
            solar = to_jalali(selected)
            st.session_state[f"{key}_year"] = solar.year
            st.session_state[language_widget_key(f"{key}_month")] = solar.month
            if not month_only:
                st.session_state[f"{key}_day"] = solar.day
        else:
            year = st.session_state.get(f"{key}_year")
            month = st.session_state.get(language_widget_key(f"{key}_month"))
            day = 1 if month_only else st.session_state.get(f"{key}_day")
            try:
                gregorian = calendar_date_to_gregorian(
                    year, month, day, "Afghan Solar Hijri"
                )
            except (TypeError, ValueError, OverflowError):
                # Invalid state can remain after a calendar/month change; reset safely.
                gregorian = datetime.now().astimezone().date()
            if gregorian:
                st.session_state[f"{key}_year"] = gregorian.year
                st.session_state[language_widget_key(f"{key}_month")] = gregorian.month
                if not month_only:
                    st.session_state[f"{key}_day"] = gregorian.day
                st.session_state[key] = gregorian
    st.session_state["_previous_calendar_type"] = new_calendar

st.set_page_config(
    page_title=t("Expense Tracker"),
    page_icon=str(LOGO_PATH),
    layout="wide",
    # Streamlit can collapse the navigation drawer automatically on narrow screens.
    initial_sidebar_state="auto",
)

st.markdown(
    """
    <style>
    .block-container { max-width: 1480px; padding-top: 1.75rem; padding-bottom: 3rem; }
    .app-brand { display:flex; align-items:center; gap:.85rem; margin:0 0 .35rem; min-width:0; }
    .app-brand img { width:48px; height:48px; flex:0 0 48px; }
    .app-brand h1 { margin:0; min-width:0; font-size:2.35rem; line-height:1.2; overflow-wrap:anywhere; }
    .stApp input, .stApp textarea, .stApp [data-baseweb="select"],
    .stApp [data-testid="stNumberInput"] { width:100%; min-width:0; max-width:100%; box-sizing:border-box; }
    .stApp [data-baseweb="select"] [role="combobox"],
    .stApp [data-testid="stWidgetLabel"] { min-width:0; overflow-wrap:anywhere; }
    [data-testid="stSidebar"] [data-testid="stSelectbox"],
    [data-testid="stSidebar"] [data-testid="stTextInput"],
    [data-testid="stSidebar"] [data-testid="stNumberInput"],
    [data-testid="stSidebar"] [data-testid="stDateInput"],
    [data-testid="stSidebar"] [data-testid="stDownloadButton"],
    [data-testid="stSidebar"] [data-testid="stButton"] { width:100%; min-width:0; }
    [data-testid="stSidebar"] [data-baseweb="select"],
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] [role="combobox"] { width:100%; min-width:0; max-width:100%; }
    [data-testid="stSidebar"] [data-baseweb="select"] [role="combobox"] { white-space:normal; overflow-wrap:anywhere; }
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] { overflow-wrap:anywhere; }
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(37,99,235,.10), rgba(16,185,129,.08));
        border: 1px solid rgba(100,116,139,.18);
        padding: 1rem 1.1rem;
        border-radius: 14px;
    }
    [data-testid="stMetricLabel"] { font-weight: 600; }
    div[data-testid="stForm"] {
        border: 1px solid rgba(100,116,139,.20);
        border-radius: 16px;
        padding: 1rem;
    }
    div.stButton > button, div.stFormSubmitButton > button {
        border-radius: 10px;
        font-weight: 600;
        min-height: 2.6rem;
    }
    @media (max-width: 768px) {
        .block-container { padding: 1rem .75rem 2rem; }
        [data-testid="stMetric"] { padding: .8rem; }
        [data-testid="stMetricValue"] { font-size: 1.25rem; }
        [data-testid="stHorizontalBlock"] {
            display: grid !important;
            grid-template-columns: minmax(0, 1fr) !important;
            gap: .75rem;
        }
        [data-testid="stHorizontalBlock"] > [data-testid="column"] {
            width: 100% !important;
            max-width: 100% !important;
            min-width: 0 !important;
            flex: none !important;
        }
    }
    @media (max-width: 1024px) {
        .block-container { padding-left: 1.25rem; padding-right: 1.25rem; }
        [data-testid="stHorizontalBlock"] > [data-testid="column"] { min-width: 0 !important; }
    }
    @media (min-width: 769px) and (max-width: 1024px) {
        [data-testid="stHorizontalBlock"] {
            display: grid !important;
            grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
            gap: .75rem;
        }
        [data-testid="stHorizontalBlock"] > [data-testid="column"] {
            width: 100% !important; max-width: 100% !important; flex: none !important;
        }
    }
    @media (max-width: 640px) {
        .block-container { padding: .8rem .65rem 1.5rem; }
        h1 { font-size: 1.65rem !important; line-height: 1.25 !important; }
        h2 { font-size: 1.35rem !important; }
        [data-baseweb="tab-list"] { overflow-x: auto !important; flex-wrap: nowrap !important; }
        [data-baseweb="tab"] { flex: 0 0 auto !important; white-space: nowrap !important; }
        [data-testid="stDataFrame"] { max-width: 100%; overflow-x: auto; }
        div[data-testid="stForm"] { padding: .75rem; }
        div.stButton > button, div.stFormSubmitButton > button { width: 100%; }
        .app-brand { gap:.6rem; }
        .app-brand img { width:40px; height:40px; flex-basis:40px; }
        .app-brand h1 { font-size:1.65rem !important; }
    }
    div[class*="st-key-update_expense_action"] button {
        background: #2563eb !important; border-color: #2563eb !important; color: #fff !important;
    }
    div[class*="st-key-update_expense_action"] button:hover {
        background: #1d4ed8 !important; border-color: #1d4ed8 !important;
    }
    div[class*="st-key-delete_expense_action"] button,
    div[class*="st-key-delete_income_action"] button {
        background: #dc2626 !important; border-color: #dc2626 !important; color: #fff !important;
    }
    div[class*="st-key-delete_expense_action"] button:hover,
    div[class*="st-key-delete_income_action"] button:hover {
        background: #b91c1c !important; border-color: #b91c1c !important;
    }
    div[class*="st-key-delete_expense_action"] button:disabled,
    div[class*="st-key-delete_income_action"] button:disabled {
        opacity: .48;
    }
    div[class*="st-key-update_expense_action"] button:focus-visible {
        outline: 3px solid #93c5fd !important; outline-offset: 2px;
    }
    div[class*="st-key-delete_expense_action"] button:focus-visible,
    div[class*="st-key-delete_income_action"] button:focus-visible {
        outline: 3px solid #fca5a5 !important; outline-offset: 2px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.sidebar.selectbox(t("Language"), LANGUAGE_OPTIONS, key="language")
if "calendar_type" not in st.session_state:
    st.session_state.calendar_type = (
        "Afghan Solar Hijri" if st.session_state.get("language") == "دری" else "Gregorian"
    )
st.sidebar.selectbox(
    t("Calendar"),
    ["Gregorian", "Afghan Solar Hijri"],
    format_func=t,
    key="calendar_type",
    on_change=sync_calendar_widget_state,
)
st.session_state.setdefault("_previous_calendar_type", st.session_state.calendar_type)
system_now = datetime.now().astimezone()
system_date = (
    format_jalali_date(system_now.date())
    if st.session_state.calendar_type == "Afghan Solar Hijri"
    else system_now.strftime("%Y-%m-%d")
)
st.sidebar.caption(
    t("System time: {date} · {time}").format(
        date=system_date, time=system_now.strftime("%H:%M %Z").strip()
    )
)
sync_language_widget_state()
if st.session_state.get("language") == "دری":
    st.markdown(
        """<style>
        @import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazir-font@v29.0.2/dist/font-face.css');
        .stApp [data-testid='stAppViewBlockContainer'],
        [data-testid='stSidebar'], [data-baseweb='tab-list'] {
            direction: rtl !important;
        }
        .stApp, .stApp *:not([data-testid='stIconMaterial']) {
            font-family: 'Vazir', Tahoma, Arial, sans-serif;
        }
        /* Streamlit icons are ligature text; keep their icon font or names render literally. */
        .stApp [data-testid='stIconMaterial'] {
            font-family: 'Material Symbols Rounded' !important;
            font-feature-settings: 'liga' 1;
            direction: ltr !important;
            writing-mode: horizontal-tb !important;
            white-space: nowrap !important;
        }
        .stApp [data-testid='stMarkdownContainer'],
        .stApp [data-testid='stWidgetLabel'], .stApp label,
        .stApp [data-testid='stCaptionContainer'],
        .stApp [data-testid='stAlert'], .stApp [data-testid='stMetricLabel'],
        .stApp [data-testid='stDataFrame'], .stApp [role='grid'],
        .stApp [role='columnheader'], .stApp [role='gridcell'] {
            direction: rtl !important; text-align: right !important;
        }
        .stApp input, .stApp textarea, .stApp [data-baseweb='select'] {
            direction: rtl !important; text-align: right !important;
        }
        .stApp button { direction: rtl !important; text-align: right !important; }
        /* Keep Streamlit's sidebar toggle in its native icon orientation. */
        [data-testid='stSidebarCollapseButton'],
        [data-testid='stSidebarCollapsedControl'],
        [data-testid='collapsedControl'],
        [data-testid='stSidebar'] button[data-testid='stBaseButton-header'],
        [data-testid='stSidebar'] button[data-testid='stBaseButton-headerNoPadding'],
        [data-testid='stSidebarCollapsedControl'] button,
        [data-testid='collapsedControl'] button {
            direction: ltr !important;
            text-align: center !important;
            writing-mode: horizontal-tb !important;
            text-orientation: mixed !important;
            white-space: nowrap !important;
            unicode-bidi: isolate !important;
        }
        [data-testid='stSidebarCollapsedControl'], [data-testid='collapsedControl'] {
            direction: ltr !important;
            writing-mode: horizontal-tb !important;
        }
        </style>""",
        unsafe_allow_html=True,
    )


def money(value):
    return f"{CURRENCY} {float(value or 0):,.2f}"


def uses_jalali_calendar():
    """Calendar choice is independent from interface language."""
    return st.session_state.get("calendar_type", "Gregorian") == "Afghan Solar Hijri"


def month_label(value):
    """Format a YYYY-MM key for the charts while keeping the data order intact."""
    year, month = (int(part) for part in str(value).split("-")[:2])
    if uses_jalali_calendar():
        return f"{AFGHAN_MONTHS[month - 1]} {year}"
    parsed = datetime.strptime(str(value), "%Y-%m")
    if st.session_state.get("language", "English") == "دری":
        return f"{t(parsed.strftime('%B'))} {year}"
    return parsed.strftime("%b %Y")


def format_month(value, format_string="%B %Y"):
    if uses_jalali_calendar():
        return format_jalali_month(value)
    if st.session_state.get("language", "English") == "دری":
        return f"{t(value.strftime('%B'))} {value.year}"
    return value.strftime(format_string)


def date_format():
    return "YYYY/MM/DD" if uses_jalali_calendar() else "MMM D, YYYY"


def app_date_input(label, value, key, help=None, month_only=False):
    """Use consistent year/month/day controls for either calendar and language."""
    is_jalali = uses_jalali_calendar()
    selected = to_jalali(value) if is_jalali else value
    columns = st.columns([2, 3] if month_only else [2, 3, 2])
    year_key, month_key = f"{key}_year", language_widget_key(f"{key}_month")
    years = list(range(selected.year - 10, selected.year + 11))
    year = int(columns[0].selectbox(
        t("Year"), years, index=years.index(selected.year), key=year_key
    ))
    month_names = AFGHAN_MONTHS if is_jalali else (
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    )
    month = int(columns[1].selectbox(
        t("Month"), range(1, 13), index=selected.month - 1,
        format_func=lambda number: t(month_names[number - 1]), key=month_key,
    ))
    if month_only:
        return calendar_date_to_gregorian(
            year, month, 1, "Afghan Solar Hijri" if is_jalali else "Gregorian"
        )

    if is_jalali:
        days = jalali_month_days(year, month)
    else:
        next_month = date(year + (month == 12), 1 if month == 12 else month + 1, 1)
        days = (next_month - timedelta(days=1)).day
    day_key = f"{key}_day"
    try:
        previous_day = int(st.session_state.get(day_key, selected.day))
    except (TypeError, ValueError):
        previous_day = selected.day
    safe_day = min(max(previous_day, 1), days)
    if day_key in st.session_state and st.session_state[day_key] != safe_day:
        st.session_state[day_key] = safe_day
    day = int(columns[2].selectbox(
        t("Day"), range(1, days + 1), index=min(selected.day, days) - 1,
        key=day_key,
    ))
    return calendar_date_to_gregorian(
        year, month, day, "Afghan Solar Hijri" if is_jalali else "Gregorian"
    )


def display_date(value):
    if uses_jalali_calendar():
        return format_jalali_date(value)
    return value


def jalali_monthly_totals(expense_rows):
    totals, by_category = {}, {}
    for row in expense_rows:
        key = jalali_month_key(row[2])
        totals[key] = totals.get(key, 0.0) + float(row[1] or 0)
        category_key = (key, row[4])
        by_category[category_key] = by_category.get(category_key, 0.0) + float(row[1] or 0)
    return (
        [(key, totals[key]) for key in sorted(totals)],
        [(month, category, amount) for (month, category), amount in sorted(by_category.items())],
    )


def gregorian_monthly_totals(expense_rows):
    """Build Gregorian monthly analytics from the already-loaded expense rows."""
    totals, by_category = {}, {}
    for row in expense_rows:
        marker = row[2]
        key = marker.strftime("%Y-%m") if hasattr(marker, "strftime") else str(marker)[:7]
        amount = float(row[1] or 0)
        totals[key] = totals.get(key, 0.0) + amount
        category_key = (key, row[4])
        by_category[category_key] = by_category.get(category_key, 0.0) + amount
    return (
        [(key, totals[key]) for key in sorted(totals)],
        [(month, category, amount) for (month, category), amount in sorted(by_category.items())],
    )


def table_rows(rows):
    return [
        {
            t("Date"): display_date(row[2]),
            t("Category"): category_label(row[4]),
            t("Reason"): row[3] or "",
            t("Amount"): float(row[1]),
        }
        for row in rows
    ]


def expense_is_valid(amount, when, reason, category):
    return validate_expense(amount, when.strftime("%Y-%m-%d"), reason, category)


def save_quick_expense():
    category_key = language_widget_key("quick_category")
    selected_category = category_option_value(
        st.session_state.get(category_key, category_option_label(NEW_CATEGORY))
    )
    category = (
        st.session_state.get("quick_custom_category", "").strip()
        if selected_category == NEW_CATEGORY
        else selected_category
    )
    amount = st.session_state.quick_amount
    if uses_jalali_calendar():
        when = calendar_date_to_gregorian(
            st.session_state.quick_date_year,
            st.session_state.quick_date_month,
            st.session_state.quick_date_day,
            "Afghan Solar Hijri",
        )
    else:
        when = calendar_date_to_gregorian(
            st.session_state.quick_date_year,
            st.session_state.quick_date_month,
            st.session_state.quick_date_day,
            "Gregorian",
        )
    reason = st.session_state.quick_reason.strip()
    if not expense_is_valid(amount, when, reason, category):
        st.session_state.quick_message = t(
            "Check the amount, date, category (1–40 characters), and reason (up to 100 characters)."
        )
        st.session_state.quick_success = False
        return
    success = add_expense(amount, when.strftime("%Y-%m-%d"), reason, category)
    st.session_state.quick_message = t(
        "Expense saved." if success else
        "Could not save the expense. Check your database connection and try again."
    )
    st.session_state.quick_success = success
    if success:
        st.session_state.quick_amount = 0.01
        current_date = datetime.now().astimezone().date()
        st.session_state.quick_date = current_date
        if uses_jalali_calendar():
            current_date = to_jalali(current_date)
        st.session_state.quick_date_year = current_date.year
        st.session_state.quick_date_month = current_date.month
        st.session_state.quick_date_day = current_date.day
        st.session_state[category_key] = category_option_label(NEW_CATEGORY)
        st.session_state.quick_custom_category = ""
        st.session_state.quick_reason = ""


logo_data = base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")
st.markdown(
    f'<div class="app-brand"><img src="data:image/svg+xml;base64,{logo_data}" '
    f'alt=""><h1>{html.escape(t("Personal Expense Tracker"))}</h1></div>',
    unsafe_allow_html=True,
)
st.caption(t("A clear view of where your money goes."))

data_error = None
try:
    # One expense read feeds the cards, categories, and charts. This avoids opening
    # several redundant database connections for aggregates of the same rows.
    expenses = get_expenses()
    total_spending = sum((Decimal(str(row[1] or 0)) for row in expenses), Decimal("0"))
    category_amounts = {}
    saved_categories = sorted({row[4] for row in expenses if row[4] and row[4].strip()})
    for row in expenses:
        category_amounts[row[4]] = category_amounts.get(
            row[4], Decimal("0")
        ) + Decimal(str(row[1] or 0))
    category_totals = sorted(
        category_amounts.items(), key=lambda item: (-item[1], str(item[0] or ""))
    )
    income_month_totals = get_income_and_spending_by_month()
    if uses_jalali_calendar():
        spending_month_totals, monthly_results = jalali_monthly_totals(expenses)
        income_totals = {}
        for marker, amount in income_month_totals:
            key = jalali_month_key(marker)
            income_totals[key] = income_totals.get(key, 0.0) + float(amount or 0)
        income_month_totals = sorted(income_totals.items())
    else:
        spending_month_totals, monthly_results = gregorian_monthly_totals(expenses)
        income_totals = {}
        for marker, amount in income_month_totals:
            key = marker.strftime("%Y-%m") if hasattr(marker, "strftime") else str(marker)[:7]
            income_totals[key] = income_totals.get(key, 0.0) + float(amount or 0)
        income_month_totals = sorted(income_totals.items())
except Exception as error:
    message, diagnostic = database_error_help(error)
    data_error = (message, diagnostic)
    expenses = []
    total_spending = Decimal("0")
    category_totals = []
    saved_categories = []
    spending_month_totals = []
    monthly_results = []
    income_month_totals = []
    income_totals = {}

if data_error:
    st.error(t(data_error[0]))
    st.caption(f"{t('Diagnostic')}: {data_error[1]}")

with st.sidebar:
    with st.expander(t("Quick add"), expanded=False, icon=":material/add_circle:"):
        # Put the common path first so quick add doesn't start in category-creation mode.
        category_options = saved_categories + [NEW_CATEGORY]
        quick_category_label = st.selectbox(
            t("Category"),
            [category_option_label(value) for value in category_options],
            key=category_widget_key("quick_category", category_options),
        )
        if category_option_value(quick_category_label) == NEW_CATEGORY:
            st.text_input(
                t("New category (when creating one)"),
                max_chars=40,
                key="quick_custom_category",
            )
        quick_date = app_date_input(t("Date"), value=datetime.now().astimezone().date(), key="quick_date")
        with st.form("quick_add_expense"):
            st.number_input(
                t("Amount"),
                min_value=0.01,
                step=1.0,
                format="%.2f",
                key="quick_amount",
            )
            st.text_input(
                t("What was it for?"),
                max_chars=100,
                placeholder=t("e.g. Lunch"),
                key="quick_reason",
            )
            st.form_submit_button(
                t("Save expense"),
                type="primary",
                on_click=save_quick_expense,
            )
        if st.session_state.get("quick_message"):
            if st.session_state.get("quick_success"):
                st.success(st.session_state.quick_message)
            else:
                st.error(st.session_state.quick_message)
    st.divider()
    with st.expander(
        t("Advanced settings"),
        expanded=False,
        icon=":material/backup:",
        key="advanced_settings",
    ):
        st.caption(t("A backup contains private financial records and is not encrypted. Keep it in a secure location."))
        if st.button(t("Create backup"), key="create_local_backup", icon=":material/save:"):
            try:
                backup_path = backup_database()
                st.session_state["created_backup_name"] = backup_path.name
                st.session_state["created_backup_data"] = backup_path.read_bytes()
                st.success(t("Backup created: {filename}").format(filename=backup_path.name))
            except Exception as error:
                st.session_state.pop("created_backup_name", None)
                st.session_state.pop("created_backup_data", None)
                st.error(t("Backup failed. Check the database connection and try again."))
                st.caption(f"{t('Diagnostic')}: {type(error).__name__}")
        if st.session_state.get("created_backup_data"):
            st.download_button(
                t("Download backup"),
                data=st.session_state["created_backup_data"],
                file_name=st.session_state["created_backup_name"],
                mime="application/json",
                key="download_created_backup",
                icon=":material/download:",
                width="stretch",
            )

overview_tab, analytics_tab, income_tab, manage_tab = st.tabs(
    [
        ":material/dashboard: " + t("Overview"),
        ":material/query_stats: " + t("Analytics"),
        ":material/payments: " + t("Income"),
        ":material/receipt_long: " + t("Manage expenses"),
    ]
)

with overview_tab:
    st.subheader(t("Monthly money at a glance"))
    selected_month = app_date_input(
        t("Choose a month"),
        value=datetime.now().astimezone().date().replace(day=1),
        key="overview_month",
        help=t("Choose a month to see that month's income and spending."),
        month_only=True,
    )
    if uses_jalali_calendar():
        month_start, month_end = jalali_month_bounds(selected_month)
    else:
        month_start = selected_month.replace(day=1)
        if month_start.month == 12:
            next_month = month_start.replace(year=month_start.year + 1, month=1)
        else:
            next_month = month_start.replace(month=month_start.month + 1)
        month_end = next_month - timedelta(days=1)
    is_jalali = uses_jalali_calendar()
    monthly_income = (
        Decimal("0") if data_error else get_monthly_income_total(
            month_start, exact=is_jalali, period_end=month_end if is_jalali else None
        )
    )
    monthly_spending = sum(
        (row[1] or 0 for row in expenses if month_start <= row[2] <= month_end),
        start=0,
    )
    remaining = monthly_income - monthly_spending
    col1, col2, col3 = st.columns(3)
    col1.metric(t("Income this month"), money(monthly_income))
    col2.metric(t("Spent this month"), money(monthly_spending))
    col3.metric(
        t("Money remaining"),
        money(remaining),
        delta=t("Within income" if remaining >= 0 else "Over income"),
        delta_color="normal" if remaining >= 0 else "inverse",
    )
    if not monthly_income:
        st.info(t("Add salary or another income in the Income tab to see your monthly balance."))
    elif remaining < 0:
        st.warning(t("Your spending is higher than the income recorded for this month."))
    st.caption(
        t("All-time spending: {amount} · {expenses} expenses · {categories} categories").format(
            amount=money(total_spending),
            expenses=f"{len(expenses):,}",
            categories=f"{len(saved_categories):,}",
        ) + f" · {format_month(month_start)}"
    )

    st.subheader(t("Expense history"))
    with st.expander(t("Find expenses"), expanded=False):
        st.caption(t("Choose a category or search descriptions to narrow this list."))
        filter_col, search_col = st.columns([1, 2])
        category_options = ["All categories"] + saved_categories
        selected_category_label = filter_col.selectbox(
            t("Filter by category"),
            [category_option_label(value) for value in category_options],
            key=category_widget_key("history_category", category_options),
        )
        selected_category = category_option_value(selected_category_label)
        search_text = search_col.text_input(
            t("Search expenses"),
            placeholder=t("Search descriptions or categories"),
            key="history_search",
        ).strip().casefold()
    search_text = search_text.strip().casefold()

    visible_expenses = [
        row for row in expenses
        if (selected_category == "All categories" or row[4] == selected_category)
        and (
            not search_text
            or search_text in (row[3] or "").casefold()
            or search_text in (row[4] or "").casefold()
        )
    ]
    if visible_expenses:
        st.dataframe(
            table_rows(visible_expenses),
            width="stretch",
            hide_index=True,
            height=420,
            column_config={
                t("Amount"): st.column_config.NumberColumn(
                    t("Amount"),
                    format=f"{CURRENCY} %,.2f",
                ),
        **({} if uses_jalali_calendar() else {
            t("Date"): st.column_config.DateColumn(t("Date"), format=date_format())
        }),
            },
        )
        st.caption(t("Showing {visible} of {total} expenses.").format(visible=len(visible_expenses), total=len(expenses)))
    elif expenses:
        st.info(t("No expenses match those filters. Clear the search or choose another category."))
        if st.button(t("Clear filters"), key="clear_history_filters"):
            st.session_state[language_widget_key("history_category")] = category_option_label("All categories")
            st.session_state.history_search = ""
            st.rerun()
    else:
        st.info(t("No expenses yet. Add your first one from Quick add."))
        st.caption(t("You can also use the Manage expenses tab for a detailed entry."))

with analytics_tab:
    st.subheader(t("Spending patterns"))
    st.caption(t("Choose a monthly view to see totals, category details, or compare income with spending."))
    if category_totals:
        st.markdown("#### " + t("Spending by category"))
        category_frame = pd.DataFrame(
            [
                {t("Category"): category_label(row[0]), t("Total spending"): float(row[1] or 0)}
                for row in category_totals
            ]
        )
        st.bar_chart(
            category_frame,
            x=t("Category"),
            y=t("Total spending"),
            color=t("Category"),
            sort=f"-{t('Total spending')}",
            height=300,
            alt=t("Total spending by category, with a distinct color for each category."),
        )
    else:
        st.info(t("Category insights will appear after you record an expense."))

    if spending_month_totals or income_month_totals:
        st.markdown("#### " + t("Monthly spending"))
        monthly_chart_options = ["Total spending", "Spending by category", "Income vs spending"]
        monthly_view_label = st.radio(
            t("Monthly chart"),
            [t(option) for option in monthly_chart_options],
            horizontal=True,
            key=language_widget_key("monthly_chart_view"),
        )
        monthly_view = source_option(monthly_view_label)
        if monthly_view == "Total spending":
            monthly_frame = pd.DataFrame([
                {t("Month"): month_label(row[0]), t("Spending"): float(row[1] or 0)}
                for row in spending_month_totals
            ])
            if not monthly_frame.empty:
                st.bar_chart(monthly_frame, x=t("Month"), y=t("Spending"), color="#2563EB", sort=False, height=300, alt=t("Total spending for each month in chronological order."))
            else:
                st.info(t("No spending recorded yet. Add expenses to see monthly totals."))
        elif monthly_view == "Spending by category":
            monthly_frame = pd.DataFrame([
                {t("Month"): month_label(row[0]), t("Category"): category_label(row[1]), t("Spending"): float(row[2] or 0)}
                for row in monthly_results
            ])
            if not monthly_frame.empty:
                st.bar_chart(monthly_frame, x=t("Month"), y=t("Spending"), color=t("Category"), stack=True, sort=False, height=300, alt=t("Monthly spending stacked by category."))
            else:
                st.info(t("No spending recorded yet. Add expenses to see category totals by month."))
        else:
            income_label = t("Income")
            spending_label = t("Spending")
            monthly_values = {str(row[0]): {income_label: 0.0, spending_label: 0.0} for row in spending_month_totals}
            for row in income_month_totals:
                monthly_values.setdefault(str(row[0]), {income_label: 0.0, spending_label: 0.0})[income_label] = float(row[1] or 0)
            for row in spending_month_totals:
                monthly_values[str(row[0])][spending_label] = float(row[1] or 0)
            comparison = pd.DataFrame([
                {t("Month"): month_label(month), **totals}
                for month, totals in sorted(monthly_values.items())
            ])
            if not comparison.empty:
                st.bar_chart(comparison, x=t("Month"), y=[income_label, spending_label], color=["#10B981", "#F97316"], stack=False, sort=False, height=300, alt=t("Monthly income and spending compared in chronological order."))
            else:
                st.info(t("Add income or expenses to compare monthly cash flow."))
    else:
        st.info(t("Monthly trends will appear after you record income or an expense."))

    st.markdown("#### " + t("Explore a date range"))
    range_col1, range_col2 = st.columns(2)
    start_date = app_date_input(
        t("From"),
        value=datetime.now().astimezone().date().replace(day=1),
        key="filter_start_date",
    )
    end_date = app_date_input(
        t("Through"),
        value=datetime.now().astimezone().date(),
        key="filter_end_date",
    )
    if start_date > end_date:
        st.warning(t("The start date must be on or before the end date."))
    else:
        range_expenses = [
            row for row in expenses if start_date <= row[2] <= end_date
        ]
        range_total = sum((row[1] for row in range_expenses), start=0)
        metric_col, detail_col = st.columns([1, 2])
        metric_col.metric(t("Spending in this period"), money(range_total))
        detail_col.metric(t("Expenses in this period"), f"{len(range_expenses):,}")
        if range_expenses:
            with st.expander(t("View expenses in this period")):
                st.dataframe(
                    table_rows(range_expenses),
                    width="stretch",
                    hide_index=True,
                    column_config={
                        t("Amount"): st.column_config.NumberColumn(
                            t("Amount"), format=f"{CURRENCY} %.2f"
                        ),
                        **({} if uses_jalali_calendar() else {
                            t("Date"): st.column_config.DateColumn(
                                t("Date"), format=date_format()
                            )
                        }),
                    },
                )
        else:
            st.info(t("No expenses were recorded in this date range."))

        daily_results = [] if data_error else get_spending_by_date_range(
            start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
        )
        if daily_results:
            daily_frame = pd.DataFrame(
                [
                    {t("Date"): display_date(row[0]), t("Daily spending"): float(row[1] or 0)}
                    for row in daily_results
                ]
            )
            st.markdown("#### " + t("Daily trend"))
            st.line_chart(
                daily_frame,
                x=t("Date"),
                y=t("Daily spending"),
                color="#10B981",
                height=260,
                alt=t("Daily spending over the selected date range."),
            )

with income_tab:
    st.subheader(t("Monthly income"))
    st.caption(t("Income is for the selected month. Add each source separately; the app adds them together."))
    income_month = app_date_input(
        t("Income month"), value=datetime.now().astimezone().date(), key="income_month", month_only=True
    )
    is_jalali = uses_jalali_calendar()
    if not is_jalali:
        income_month = income_month.replace(day=1)
        income_period_end = None
    else:
        _, income_period_end = jalali_month_bounds(income_month)
    with st.form("add_income_form"):
        income_source = st.text_input(t("Source"), max_chars=80, placeholder=t("e.g. Salary, freelance work"))
        income_amount = st.number_input(t("Amount"), min_value=0.01, step=1.0, format="%.2f", key="income_amount")
        income_submitted = st.form_submit_button(
            t("Add income"), type="primary", icon=":material/add_circle:"
        )
    if income_submitted:
        if not validate_income(income_amount, income_month, income_source, exact=is_jalali):
            st.error(t("Enter a positive amount and an income source of 1–80 characters."))
        elif add_monthly_income(income_amount, income_month, income_source, exact=is_jalali):
            st.toast(t("Income added successfully."), icon=":material/check_circle:")
            st.rerun()
        else:
            st.error(t("Could not save income. Check the database connection and confirm income.sql has been applied."))
    month_income_rows = [] if data_error else get_monthly_income_entries(
        income_month, exact=is_jalali, period_end=income_period_end
    )
    st.metric(
        t("Total income · {month}").format(month=format_month(income_month)),
        money(Decimal("0") if data_error else get_monthly_income_total(
            income_month, exact=is_jalali, period_end=income_period_end
        )),
    )
    if month_income_rows:
        st.dataframe([{t("Source"): row[1], t("Amount"): float(row[2])} for row in month_income_rows], width="stretch", hide_index=True, column_config={t("Amount"): st.column_config.NumberColumn(t("Amount"), format=f"{CURRENCY} %,.2f")})
        income_options = {f"{row[1]} · {money(row[2])}": row[0] for row in month_income_rows}
        income_to_delete = st.selectbox(t("Remove an income entry"), list(income_options), key="income_delete_select")
        confirm_income_delete = st.checkbox(t("I understand this permanently deletes the selected income."), key="confirm_income_delete")
        with st.container(key="delete_income_action"):
            if st.button(t("Delete income"), disabled=not confirm_income_delete, key="delete_income_button", icon=":material/delete:"):
                if delete_monthly_income(income_options[income_to_delete]):
                    st.toast(t("Income entry deleted."), icon=":material/delete:")
                    st.rerun()
                else:
                    st.error(t("Could not delete income. Refresh and try again."))
    else:
        st.info(t("No income recorded for this month. Add salary or another source above."))

with manage_tab:
    st.caption(t("Manage your expenses here. Add a new record, update an existing one, or delete it after confirmation."))
    add_tab, update_tab, delete_tab = st.tabs(
        [
            ":material/add_circle: " + t("Add expense"),
            ":material/edit: " + t("Update expense"),
            ":material/delete: " + t("Delete expense"),
        ]
    )

    with add_tab:
        st.markdown("#### " + t("Add a detailed expense"))
        st.caption(t("Choose a category. The extra field appears only when you create a new category."))
        # Prefer an existing category; users can still choose the final "new" option.
        category_options = saved_categories + [NEW_CATEGORY]
        category_choice_label = st.selectbox(
            t("Category"),
            [category_option_label(value) for value in category_options],
            key=category_widget_key("add_category_choice", category_options),
        )
        category_choice = category_option_value(category_choice_label)
        if category_choice == NEW_CATEGORY:
            custom_category = st.text_input(
                t("New category (when creating one)"),
                max_chars=40,
                key="add_custom_category",
            )
        else:
            custom_category = ""
        expense_date = app_date_input(t("Date"), value=datetime.now().astimezone().date(), key="add_date")
        with st.form("add_expense_form"):
            amount = st.number_input(
                t("Amount"),
                min_value=0.01,
                step=1.0,
                format="%.2f",
                key="add_amount",
            )
            reason = st.text_input(
                t("What was it for?"),
                max_chars=100,
                placeholder=t("e.g. Groceries"),
                key="add_reason",
            )
            submitted = st.form_submit_button(
                t("Save expense"), type="primary", icon=":material/add_circle:"
            )
        if submitted:
            category = (
                custom_category.strip()
                if category_choice == NEW_CATEGORY
                else category_choice
            )
            if not expense_is_valid(amount, expense_date, reason, category):
                st.error(t("Check the amount, date, category (1–40 characters), and reason (up to 100 characters)."))
            elif add_expense(
                amount,
                expense_date.strftime("%Y-%m-%d"),
                reason,
                category,
            ):
                st.toast(t("Expense added successfully."), icon=":material/check_circle:")
                st.rerun()
            else:
                st.error(t("Could not save the expense. Check your database connection."))

    with update_tab:
        if not expenses:
            st.info(t("Add an expense first; it will appear here for editing."))
        else:
            expense_options = {
                f"{display_date(row[2])} · {category_label(row[4])} · {money(row[1])} · {row[3] or t('No description')}": row
                for row in expenses
            }
            selected_label = st.selectbox(
                t("Choose an expense"),
                list(expense_options),
                key="update_expense_select",
            )
            selected_expense = expense_options[selected_label]
            st.caption(t("Choose a category. The extra field appears only when you create a new category."))
            existing_categories = list(saved_categories)
            if selected_expense[4] not in existing_categories:
                existing_categories.append(selected_expense[4])
            update_category_options = [selected_expense[4]] + [
                value for value in existing_categories if value != selected_expense[4]
            ] + [NEW_CATEGORY]
            update_category_choice_label = st.selectbox(
                t("Category"),
                [category_option_label(value) for value in update_category_options],
                key=category_widget_key("update_category_choice", update_category_options),
            )
            update_category_choice = category_option_value(update_category_choice_label)
            if update_category_choice == NEW_CATEGORY:
                st.text_input(
                    t("New category (when creating one)"),
                    max_chars=40,
                    key="update_custom_category",
                )
            new_date = app_date_input(
                t("Date"), value=selected_expense[2], key="update_date"
            )
            with st.form("update_expense_form"):
                new_amount = st.number_input(
                    t("Amount"),
                    min_value=0.01,
                    value=float(selected_expense[1]),
                    step=1.0,
                    format="%.2f",
                    key="update_amount",
                )
                new_reason = st.text_input(
                    t("What was it for?"),
                    value=selected_expense[3] or "",
                    max_chars=100,
                    key="update_reason",
                )
                with st.container(key="update_expense_action"):
                    update_submitted = st.form_submit_button(
                        t("Save changes"), type="primary", icon=":material/save:"
                    )
            if update_submitted:
                new_category = (
                    st.session_state.get("update_custom_category", "").strip()
                    if update_category_choice == NEW_CATEGORY
                    else update_category_choice
                )
                if not expense_is_valid(new_amount, new_date, new_reason, new_category):
                    st.error(t("Check the amount, date, category (1–40 characters), and reason (up to 100 characters)."))
                elif update_expense(
                    selected_expense[0],
                    new_amount,
                    new_date.strftime("%Y-%m-%d"),
                    new_reason,
                    new_category,
                ):
                    st.toast(t("Expense updated successfully."), icon=":material/check_circle:")
                    st.rerun()
                else:
                    st.error(t("Could not update the expense. Refresh and try again."))

    with delete_tab:
        if not expenses:
            st.info(t("There are no expenses to delete."))
        else:
            delete_options = {
                f"{display_date(row[2])} · {category_label(row[4])} · {money(row[1])} · {row[3] or t('No description')}": row[0]
                for row in expenses
            }
            selected_delete_label = st.selectbox(
                t("Choose an expense"),
                list(delete_options),
                key="delete_expense_select",
            )
            confirm_delete = st.checkbox(
                t("I understand this permanently deletes the selected expense."),
                key="confirm_delete",
            )
            with st.container(key="delete_expense_action"):
                if st.button(
                    t("Delete expense"),
                    type="primary",
                    disabled=not confirm_delete,
                    key="delete_expense_button",
                    icon=":material/delete:",
                ):
                    if delete_expense(delete_options[selected_delete_label]):
                        st.toast(t("Expense deleted."), icon=":material/delete:")
                        st.rerun()
                    else:
                        st.error(t("Could not delete the expense. Refresh and try again."))
