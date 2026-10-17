import os
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

from database_errors import database_error_help
from expenses import (
    add_expense,
    add_monthly_income,
    delete_expense,
    delete_monthly_income,
    get_categories,
    get_expenses,
    get_income_and_spending_by_month,
    get_monthly_income_entries,
    get_monthly_income_total,
    get_monthly_spending_totals,
    get_monthly_spending_by_category,
    get_spending_by_category,
    get_spending_by_date_range,
    get_total_spending,
    update_expense,
    validate_expense,
    validate_income,
)

CURRENCY = os.getenv("EXPENSE_CURRENCY", "AFN").upper()
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
    "Category": "دسته‌بندی",
    "New category (when creating one)": "دسته‌بندی جدید (برای ساختن دسته‌بندی)",
    "What was it for?": "این مصرف برای چه بود؟",
    "e.g. Lunch": "مثلاً ناهار",
    "Save expense": "ثبت مصرف",
    "Expense saved.": "مصرف ثبت شد.",
    "Could not save the expense. Check your database connection and try again.": "مصرف ثبت نشد. اتصال پایگاه داده را بررسی و دوباره تلاش کنید.",
    "Check the amount, date, category (1–40 characters), and reason (up to 100 characters).": "مقدار، تاریخ، دسته‌بندی (۱ تا ۴۰ نویسه) و توضیح (حداکثر ۱۰۰ نویسه) را بررسی کنید.",
    "Language": "زبان",
    "Diagnostic": "تشخیص",
    "Could not connect to the configured MySQL server. Start MySQL/MariaDB and verify EXPENSE_DB_HOST and EXPENSE_DB_PORT.": "اتصال به سرور MySQL ممکن نشد. MySQL/MariaDB را روشن کرده و EXPENSE_DB_HOST و EXPENSE_DB_PORT را بررسی کنید.",
    "MySQL rejected the login. Verify EXPENSE_DB_USER and EXPENSE_DB_PASSWORD.": "ورود به MySQL رد شد. EXPENSE_DB_USER و EXPENSE_DB_PASSWORD را بررسی کنید.",
    "The configured database does not exist. Create expense_tracker or set EXPENSE_DB_NAME to the correct database.": "پایگاه دادهٔ تنظیم‌شده وجود ندارد. expense_tracker را بسازید یا EXPENSE_DB_NAME را درست تنظیم کنید.",
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
    "Choose any day in a month to see that month's income and spending.": "هر روزی از ماه را انتخاب کنید تا درآمد و مصارف همان ماه را ببینید.",
    "Income this month": "درآمد این ماه",
    "Spent this month": "مصرف‌شده در این ماه",
    "Money remaining": "پول باقی‌مانده",
    "Within income": "در محدودهٔ درآمد",
    "Over income": "بیشتر از درآمد",
    "Add salary or another income in the Income tab to see your monthly balance.": "برای دیدن توازن ماهانه، معاش یا درآمد دیگری را در بخش «درآمد» ثبت کنید.",
    "Your spending is higher than the income recorded for this month.": "مصارف شما از درآمد ثبت‌شدهٔ این ماه بیشتر است.",
    "All-time spending: {amount} · {expenses} expenses · {categories} categories": "مجموع مصارف: {amount} · {expenses} مصرف · {categories} دسته‌بندی",
    "Expense history": "تاریخچهٔ مصارف",
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


def category_label(value):
    """Translate familiar category names for display without changing stored values."""
    if st.session_state.get("language", "English") == "دری":
        return CATEGORY_TRANSLATIONS.get(str(value).strip().upper(), value)
    return value


def category_option_label(value):
    if value in (NEW_CATEGORY, "All categories"):
        return t(value)
    return category_label(value)

st.set_page_config(
    page_title=t("Expense Tracker"),
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container { max-width: 1480px; padding-top: 1.75rem; padding-bottom: 3rem; }
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
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.sidebar.selectbox(t("Language"), LANGUAGE_OPTIONS, key="language")
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


def month_label(value):
    """Format a YYYY-MM key for the charts while keeping the data order intact."""
    parsed = datetime.strptime(str(value), "%Y-%m")
    if st.session_state.get("language", "English") == "دری":
        dari_months = ["جنوری", "فبروری", "مارچ", "اپریل", "می", "جون", "جولای", "آگست", "سپتامبر", "اکتوبر", "نوامبر", "دسامبر"]
        return f"{dari_months[parsed.month - 1]} {parsed.year}"
    return parsed.strftime("%b %Y")


def format_month(value, format_string="%B %Y"):
    if st.session_state.get("language", "English") == "دری":
        return month_label(value.strftime("%Y-%m"))
    return value.strftime(format_string)


def date_format():
    return "YYYY/MM/DD" if st.session_state.get("language") == "دری" else "MMM D, YYYY"


def table_rows(rows):
    return [
        {
            t("Date"): row[2],
            t("Category"): category_label(row[4]),
            t("Reason"): row[3] or "",
            t("Amount"): float(row[1]),
        }
        for row in rows
    ]


def expense_is_valid(amount, when, reason, category):
    return validate_expense(amount, when.strftime("%Y-%m-%d"), reason, category)


def save_quick_expense():
    category = (
        st.session_state.quick_custom_category.strip()
        if st.session_state.quick_category == NEW_CATEGORY
        else st.session_state.quick_category
    )
    amount = st.session_state.quick_amount
    when = st.session_state.quick_date
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
        st.session_state.quick_date = date.today()
        st.session_state.quick_category = NEW_CATEGORY
        st.session_state.quick_custom_category = ""
        st.session_state.quick_reason = ""


st.title("💰 " + t("Personal Expense Tracker"))
st.caption(t("A clear view of where your money goes."))

try:
    expenses = get_expenses()
    total_spending = get_total_spending()
    category_totals = get_spending_by_category()
    saved_categories = [row[0] for row in get_categories()]
    monthly_results = get_monthly_spending_by_category()
    spending_month_totals = get_monthly_spending_totals()
    income_month_totals = get_income_and_spending_by_month()
except Exception as error:
    message, diagnostic = database_error_help(error)
    st.error(t(message))
    st.caption(f"{t('Diagnostic')}: {diagnostic}")
    st.stop()

with st.sidebar:
    with st.expander(t("Quick add"), expanded=False):
        st.caption(t("Capture an expense without leaving your current view."))
        with st.form("quick_add_expense"):
            st.number_input(
                t("Amount"),
                min_value=0.01,
                step=1.0,
                format="%.2f",
                key="quick_amount",
            )
            st.date_input(t("Date"), value=date.today(), key="quick_date")
            st.selectbox(
                t("Category"),
                [NEW_CATEGORY] + saved_categories,
                key="quick_category",
                format_func=category_option_label,
            )
            st.text_input(
                t("New category (when creating one)"),
                max_chars=40,
                key="quick_custom_category",
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
    st.caption(t("Currency display: {currency}").format(currency=CURRENCY))
    st.caption(t("Change it with the EXPENSE_CURRENCY environment variable."))

overview_tab, analytics_tab, income_tab, manage_tab = st.tabs(
    [t("Overview"), t("Analytics"), t("Income"), t("Manage expenses")]
)

with overview_tab:
    st.subheader(t("Monthly money at a glance"))
    selected_month = st.date_input(
        t("Choose a month"),
        value=date.today().replace(day=1),
        key="overview_month",
        help=t("Choose any day in a month to see that month's income and spending."),
    )
    month_start = selected_month.replace(day=1)
    if month_start.month == 12:
        next_month = month_start.replace(year=month_start.year + 1, month=1)
    else:
        next_month = month_start.replace(month=month_start.month + 1)
    month_end = next_month - timedelta(days=1)
    monthly_income = get_monthly_income_total(month_start)
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
    filter_col, search_col = st.columns([1, 2])
    selected_category = filter_col.selectbox(
        t("Filter by category"),
        ["All categories"] + saved_categories,
        key="history_category",
        format_func=category_option_label,
    )
    search_text = search_col.text_input(
        t("Search expenses"),
        placeholder=t("Search descriptions or categories"),
        key="history_search",
    ).strip().casefold()

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
            use_container_width=True,
            hide_index=True,
            height=420,
            column_config={
                t("Amount"): st.column_config.NumberColumn(
                    t("Amount"),
                    format=f"{CURRENCY} %,.2f",
                ),
                t("Date"): st.column_config.DateColumn(t("Date"), format=date_format()),
            },
        )
        st.caption(t("Showing {visible} of {total} expenses.").format(visible=len(visible_expenses), total=len(expenses)))
    elif expenses:
        st.info(t("No expenses match those filters. Clear the search or choose another category."))
    else:
        st.info(t("No expenses yet. Add your first one from Quick add."))
        st.caption(t("You can also use the Manage expenses tab for a detailed entry."))

with analytics_tab:
    st.subheader(t("Spending patterns"))
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
        monthly_view = st.radio(
            t("Monthly chart"),
            ["Total spending", "Spending by category", "Income vs spending"],
            horizontal=True,
            key="monthly_chart_view",
            format_func=t,
        )
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
    start_date = range_col1.date_input(
        t("From"),
        value=date.today().replace(day=1),
        key="filter_start_date",
    )
    end_date = range_col2.date_input(
        t("Through"),
        value=date.today(),
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
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        t("Amount"): st.column_config.NumberColumn(
                            t("Amount"), format=f"{CURRENCY} %.2f"
                        ),
                        t("Date"): st.column_config.DateColumn(
                            t("Date"), format=date_format()
                        ),
                    },
                )
        else:
            st.info(t("No expenses were recorded in this date range."))

        daily_results = get_spending_by_date_range(
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d"),
        )
        if daily_results:
            daily_frame = pd.DataFrame(
                [
                    {t("Date"): row[0], t("Daily spending"): float(row[1] or 0)}
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
    st.caption(t("Record each income source for a month. Multiple entries are added together in your balance."))
    income_month = st.date_input(t("Income month"), value=date.today().replace(day=1), key="income_month")
    income_month = income_month.replace(day=1)
    with st.form("add_income_form"):
        income_source = st.text_input(t("Source"), max_chars=80, placeholder=t("e.g. Salary, freelance work"))
        income_amount = st.number_input(t("Amount"), min_value=0.01, step=1.0, format="%.2f", key="income_amount")
        income_submitted = st.form_submit_button(t("Add income"), type="primary")
    if income_submitted:
        if not validate_income(income_amount, income_month, income_source):
            st.error(t("Enter a positive amount and an income source of 1–80 characters."))
        elif add_monthly_income(income_amount, income_month, income_source):
            st.toast(t("Income added successfully."), icon="✅")
            st.rerun()
        else:
            st.error(t("Could not save income. Check the database connection and confirm income.sql has been applied."))
    month_income_rows = get_monthly_income_entries(income_month)
    st.metric(t("Total income · {month}").format(month=format_month(income_month)), money(get_monthly_income_total(income_month)))
    if month_income_rows:
        st.dataframe([{t("Source"): row[1], t("Amount"): float(row[2])} for row in month_income_rows], use_container_width=True, hide_index=True, column_config={t("Amount"): st.column_config.NumberColumn(t("Amount"), format=f"{CURRENCY} %,.2f")})
        income_options = {f"{row[1]} · {money(row[2])}": row[0] for row in month_income_rows}
        income_to_delete = st.selectbox(t("Remove an income entry"), list(income_options), key="income_delete_select")
        confirm_income_delete = st.checkbox(t("I understand this permanently deletes the selected income."), key="confirm_income_delete")
        if st.button(t("Delete income"), disabled=not confirm_income_delete, key="delete_income_button"):
            if delete_monthly_income(income_options[income_to_delete]):
                st.toast(t("Income entry deleted."), icon="🗑️")
                st.rerun()
            else:
                st.error(t("Could not delete income. Refresh and try again."))
    else:
        st.info(t("No income recorded for this month. Add salary or another source above."))

with manage_tab:
    add_tab, update_tab, delete_tab = st.tabs(
        [t("Add expense"), t("Update expense"), t("Delete expense")]
    )

    with add_tab:
        st.markdown("#### " + t("Add a detailed expense"))
        with st.form("add_expense_form"):
            amount = st.number_input(
                t("Amount"),
                min_value=0.01,
                step=1.0,
                format="%.2f",
                key="add_amount",
            )
            expense_date = st.date_input(
                t("Date"),
                value=date.today(),
                key="add_date",
            )
            reason = st.text_input(
                t("What was it for?"),
                max_chars=100,
                placeholder=t("e.g. Groceries"),
                key="add_reason",
            )
            category_choice = st.selectbox(
                t("Category"),
                [NEW_CATEGORY] + saved_categories,
                key="add_category_choice",
                format_func=category_option_label,
            )
            custom_category = st.text_input(
                t("New category (when creating one)"),
                max_chars=40,
                key="add_custom_category",
            )
            submitted = st.form_submit_button(t("Save expense"), type="primary")
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
                st.toast(t("Expense added successfully."), icon="✅")
                st.rerun()
            else:
                st.error(t("Could not save the expense. Check your database connection."))

    with update_tab:
        if not expenses:
            st.info(t("Add an expense first; it will appear here for editing."))
        else:
            expense_options = {
                f"{row[2]} · {category_label(row[4])} · {money(row[1])} · {row[3] or t('No description')}": row
                for row in expenses
            }
            selected_label = st.selectbox(
                t("Choose an expense"),
                list(expense_options),
                key="update_expense_select",
            )
            selected_expense = expense_options[selected_label]
            with st.form("update_expense_form"):
                new_amount = st.number_input(
                    t("Amount"),
                    min_value=0.01,
                    value=float(selected_expense[1]),
                    step=1.0,
                    format="%.2f",
                    key="update_amount",
                )
                new_date = st.date_input(
                    t("Date"),
                    value=selected_expense[2],
                    key="update_date",
                )
                new_reason = st.text_input(
                    t("What was it for?"),
                    value=selected_expense[3] or "",
                    max_chars=100,
                    key="update_reason",
                )
                existing_categories = list(saved_categories)
                if selected_expense[4] not in existing_categories:
                    existing_categories.append(selected_expense[4])
                update_category_choice = st.selectbox(
                    t("Category"),
                    [NEW_CATEGORY] + existing_categories,
                    index=existing_categories.index(selected_expense[4]) + 1,
                    key="update_category_choice",
                    format_func=category_option_label,
                )
                new_custom_category = st.text_input(
                    t("New category (when creating one)"),
                    max_chars=40,
                    key="update_custom_category",
                )
                update_submitted = st.form_submit_button(
                    t("Save changes"), type="primary"
                )
            if update_submitted:
                new_category = (
                    new_custom_category.strip()
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
                    st.toast(t("Expense updated successfully."), icon="✅")
                    st.rerun()
                else:
                    st.error(t("Could not update the expense. Refresh and try again."))

    with delete_tab:
        if not expenses:
            st.info(t("There are no expenses to delete."))
        else:
            delete_options = {
                f"{row[2]} · {category_label(row[4])} · {money(row[1])} · {row[3] or t('No description')}": row[0]
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
            if st.button(
                t("Delete expense"),
                type="primary",
                disabled=not confirm_delete,
                key="delete_expense_button",
            ):
                if delete_expense(delete_options[selected_delete_label]):
                    st.toast(t("Expense deleted."), icon="🗑️")
                    st.rerun()
                else:
                    st.error(t("Could not delete the expense. Refresh and try again."))
