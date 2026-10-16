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

st.set_page_config(
    page_title="Expense Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container { padding-top: 2rem; padding-bottom: 3rem; }
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(37,99,235,.10), rgba(16,185,129,.08));
        border: 1px solid rgba(100,116,139,.18);
        padding: 1rem 1.1rem;
        border-radius: 16px;
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
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def money(value):
    return f"{CURRENCY} {float(value or 0):,.2f}"


def month_label(value):
    """Format a YYYY-MM key for the charts while keeping the data order intact."""
    return datetime.strptime(str(value), "%Y-%m").strftime("%b %Y")


def table_rows(rows):
    return [
        {
            "Date": row[2],
            "Category": row[4],
            "Reason": row[3] or "",
            "Amount": float(row[1]),
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
        st.session_state.quick_message = (
            "Check the amount, date, category (1–40 characters), "
            "and reason (up to 100 characters)."
        )
        st.session_state.quick_success = False
        return
    success = add_expense(amount, when.strftime("%Y-%m-%d"), reason, category)
    st.session_state.quick_message = (
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


st.title("💰 Personal Expense Tracker")
st.caption("A clear view of where your money goes.")

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
    st.error(message)
    st.caption(f"Diagnostic: {diagnostic}")
    st.stop()

with st.sidebar:
    st.title("Quick add")
    st.caption("Capture an expense without leaving your current view.")
    with st.form("quick_add_expense"):
        st.number_input(
            "Amount",
            min_value=0.01,
            step=1.0,
            format="%.2f",
            key="quick_amount",
        )
        st.date_input("Date", value=date.today(), key="quick_date")
        st.selectbox(
            "Category",
            [NEW_CATEGORY] + saved_categories,
            key="quick_category",
        )
        st.text_input(
            "New category (when creating one)",
            max_chars=40,
            key="quick_custom_category",
        )
        st.text_input(
            "What was it for?",
            max_chars=100,
            placeholder="e.g. Lunch",
            key="quick_reason",
        )
        st.form_submit_button(
            "Save expense",
            type="primary",
            on_click=save_quick_expense,
        )
    if st.session_state.get("quick_message"):
        if st.session_state.get("quick_success"):
            st.success(st.session_state.quick_message)
        else:
            st.error(st.session_state.quick_message)
    st.divider()
    st.caption(f"Currency display: {CURRENCY}")
    st.caption("Change it with the EXPENSE_CURRENCY environment variable.")

overview_tab, analytics_tab, income_tab, manage_tab = st.tabs(
    ["Overview", "Analytics", "Income", "Manage expenses"]
)

with overview_tab:
    st.subheader("Monthly money at a glance")
    selected_month = st.date_input(
        "Choose a month",
        value=date.today().replace(day=1),
        key="overview_month",
        help="Choose any day in a month to see that month's income and spending.",
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
    col1.metric("Income this month", money(monthly_income))
    col2.metric("Spent this month", money(monthly_spending))
    col3.metric(
        "Money remaining",
        money(remaining),
        delta="Within income" if remaining >= 0 else "Over income",
        delta_color="normal" if remaining >= 0 else "inverse",
    )
    if not monthly_income:
        st.info("Add salary or another income in the Income tab to see your monthly balance.")
    elif remaining < 0:
        st.warning("Your spending is higher than the income recorded for this month.")
    st.caption(
        f"{month_start.strftime('%B %Y')} · All-time spending: {money(total_spending)} · "
        f"{len(expenses):,} expenses · {len(saved_categories):,} categories"
    )

    st.subheader("Expense history")
    filter_col, search_col = st.columns([1, 2])
    selected_category = filter_col.selectbox(
        "Filter by category",
        ["All categories"] + saved_categories,
        key="history_category",
    )
    search_text = search_col.text_input(
        "Search expenses",
        placeholder="Search descriptions or categories",
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
            column_config={
                "Amount": st.column_config.NumberColumn(
                    "Amount",
                    format=f"{CURRENCY} %,.2f",
                ),
                "Date": st.column_config.DateColumn("Date", format="MMM D, YYYY"),
            },
        )
        st.caption(f"Showing {len(visible_expenses)} of {len(expenses)} expenses.")
    elif expenses:
        st.info("No expenses match those filters. Clear the search or choose another category.")
    else:
        st.info("No expenses yet. Add your first one from Quick add.")
        st.caption("You can also use the Manage expenses tab for a detailed entry.")

with analytics_tab:
    st.subheader("Spending patterns")
    if category_totals:
        st.markdown("#### Spending by category")
        category_frame = pd.DataFrame(
            [
                {"Category": row[0], "Total spending": float(row[1] or 0)}
                for row in category_totals
            ]
        )
        st.bar_chart(
            category_frame,
            x="Category",
            y="Total spending",
            color="Category",
            sort="-Total spending",
            height=300,
            alt="Total spending by category, with a distinct color for each category.",
        )
    else:
        st.info("Category insights will appear after you record an expense.")

    if spending_month_totals or income_month_totals:
        st.markdown("#### Monthly spending")
        monthly_view = st.radio(
            "Monthly chart",
            ["Total spending", "Spending by category", "Income vs spending"],
            horizontal=True,
            key="monthly_chart_view",
        )
        if monthly_view == "Total spending":
            monthly_frame = pd.DataFrame([
                {"Month": month_label(row[0]), "Spending": float(row[1] or 0)}
                for row in spending_month_totals
            ])
            if not monthly_frame.empty:
                st.bar_chart(monthly_frame, x="Month", y="Spending", color="#2563EB", sort=False, height=300, alt="Total spending for each month in chronological order.")
            else:
                st.info("No spending recorded yet. Add expenses to see monthly totals.")
        elif monthly_view == "Spending by category":
            monthly_frame = pd.DataFrame([
                {"Month": month_label(row[0]), "Category": row[1], "Spending": float(row[2] or 0)}
                for row in monthly_results
            ])
            if not monthly_frame.empty:
                st.bar_chart(monthly_frame, x="Month", y="Spending", color="Category", stack=True, sort=False, height=300, alt="Monthly spending stacked by category.")
            else:
                st.info("No spending recorded yet. Add expenses to see category totals by month.")
        else:
            monthly_values = {str(row[0]): {"Income": 0.0, "Spending": 0.0} for row in spending_month_totals}
            for row in income_month_totals:
                monthly_values.setdefault(str(row[0]), {"Income": 0.0, "Spending": 0.0})["Income"] = float(row[1] or 0)
            for row in spending_month_totals:
                monthly_values[str(row[0])]["Spending"] = float(row[1] or 0)
            comparison = pd.DataFrame([
                {"Month": month_label(month), **totals}
                for month, totals in sorted(monthly_values.items())
            ])
            if not comparison.empty:
                st.bar_chart(comparison, x="Month", y=["Income", "Spending"], color=["#10B981", "#F97316"], stack=False, sort=False, height=300, alt="Monthly income and spending compared in chronological order.")
            else:
                st.info("Add income or expenses to compare monthly cash flow.")
    else:
        st.info("Monthly trends will appear after you record income or an expense.")

    st.markdown("#### Explore a date range")
    range_col1, range_col2 = st.columns(2)
    start_date = range_col1.date_input(
        "From",
        value=date.today().replace(day=1),
        key="filter_start_date",
    )
    end_date = range_col2.date_input(
        "Through",
        value=date.today(),
        key="filter_end_date",
    )
    if start_date > end_date:
        st.warning("The start date must be on or before the end date.")
    else:
        range_expenses = [
            row for row in expenses if start_date <= row[2] <= end_date
        ]
        range_total = sum((row[1] for row in range_expenses), start=0)
        metric_col, detail_col = st.columns([1, 2])
        metric_col.metric("Spending in this period", money(range_total))
        detail_col.metric("Expenses in this period", f"{len(range_expenses):,}")
        if range_expenses:
            with st.expander("View expenses in this period"):
                st.dataframe(
                    table_rows(range_expenses),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Amount": st.column_config.NumberColumn(
                            "Amount", format=f"{CURRENCY} %.2f"
                        ),
                        "Date": st.column_config.DateColumn(
                            "Date", format="MMM D, YYYY"
                        ),
                    },
                )
        else:
            st.info("No expenses were recorded in this date range.")

        daily_results = get_spending_by_date_range(
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d"),
        )
        if daily_results:
            daily_frame = pd.DataFrame(
                [
                    {"Date": row[0], "Daily spending": float(row[1] or 0)}
                    for row in daily_results
                ]
            )
            st.markdown("#### Daily trend")
            st.line_chart(
                daily_frame,
                x="Date",
                y="Daily spending",
                color="#10B981",
                height=260,
                alt="Daily spending over the selected date range.",
            )

with income_tab:
    st.subheader("Monthly income")
    st.caption("Record each income source for a month. Multiple entries are added together in your balance.")
    income_month = st.date_input("Income month", value=date.today().replace(day=1), key="income_month")
    income_month = income_month.replace(day=1)
    with st.form("add_income_form"):
        income_source = st.text_input("Source", max_chars=80, placeholder="e.g. Salary, freelance work")
        income_amount = st.number_input("Amount", min_value=0.01, step=1.0, format="%.2f", key="income_amount")
        income_submitted = st.form_submit_button("Add income", type="primary")
    if income_submitted:
        if not validate_income(income_amount, income_month, income_source):
            st.error("Enter a positive amount and an income source of 1–80 characters.")
        elif add_monthly_income(income_amount, income_month, income_source):
            st.toast("Income added successfully.", icon="✅")
            st.rerun()
        else:
            st.error("Could not save income. Check the database connection and confirm income.sql has been applied.")
    month_income_rows = get_monthly_income_entries(income_month)
    st.metric(f"Total income · {income_month.strftime('%B %Y')}", money(get_monthly_income_total(income_month)))
    if month_income_rows:
        st.dataframe([{"Source": row[1], "Amount": float(row[2])} for row in month_income_rows], use_container_width=True, hide_index=True, column_config={"Amount": st.column_config.NumberColumn("Amount", format=f"{CURRENCY} %,.2f")})
        income_options = {f"{row[1]} · {money(row[2])}": row[0] for row in month_income_rows}
        income_to_delete = st.selectbox("Remove an income entry", list(income_options), key="income_delete_select")
        confirm_income_delete = st.checkbox("I understand this permanently deletes the selected income.", key="confirm_income_delete")
        if st.button("Delete income", disabled=not confirm_income_delete, key="delete_income_button"):
            if delete_monthly_income(income_options[income_to_delete]):
                st.toast("Income entry deleted.", icon="🗑️")
                st.rerun()
            else:
                st.error("Could not delete income. Refresh and try again.")
    else:
        st.info("No income recorded for this month. Add salary or another source above.")

with manage_tab:
    add_tab, update_tab, delete_tab = st.tabs(
        ["Add expense", "Update expense", "Delete expense"]
    )

    with add_tab:
        st.markdown("#### Add a detailed expense")
        with st.form("add_expense_form"):
            amount = st.number_input(
                "Amount",
                min_value=0.01,
                step=1.0,
                format="%.2f",
                key="add_amount",
            )
            expense_date = st.date_input(
                "Date",
                value=date.today(),
                key="add_date",
            )
            reason = st.text_input(
                "What was it for?",
                max_chars=100,
                placeholder="e.g. Groceries",
                key="add_reason",
            )
            category_choice = st.selectbox(
                "Category",
                [NEW_CATEGORY] + saved_categories,
                key="add_category_choice",
            )
            custom_category = st.text_input(
                "New category (when creating one)",
                max_chars=40,
                key="add_custom_category",
            )
            submitted = st.form_submit_button("Save expense", type="primary")
        if submitted:
            category = (
                custom_category.strip()
                if category_choice == NEW_CATEGORY
                else category_choice
            )
            if not expense_is_valid(amount, expense_date, reason, category):
                st.error(
                    "Check the amount, date, category (1–40 characters), "
                    "and reason (up to 100 characters)."
                )
            elif add_expense(
                amount,
                expense_date.strftime("%Y-%m-%d"),
                reason,
                category,
            ):
                st.toast("Expense added successfully.", icon="✅")
                st.rerun()
            else:
                st.error("Could not save the expense. Check your database connection.")

    with update_tab:
        if not expenses:
            st.info("Add an expense first; it will appear here for editing.")
        else:
            expense_options = {
                f"{row[2]} · {row[4]} · {money(row[1])} · {row[3] or 'No description'}": row
                for row in expenses
            }
            selected_label = st.selectbox(
                "Choose an expense",
                list(expense_options),
                key="update_expense_select",
            )
            selected_expense = expense_options[selected_label]
            with st.form("update_expense_form"):
                new_amount = st.number_input(
                    "Amount",
                    min_value=0.01,
                    value=float(selected_expense[1]),
                    step=1.0,
                    format="%.2f",
                    key="update_amount",
                )
                new_date = st.date_input(
                    "Date",
                    value=selected_expense[2],
                    key="update_date",
                )
                new_reason = st.text_input(
                    "What was it for?",
                    value=selected_expense[3] or "",
                    max_chars=100,
                    key="update_reason",
                )
                existing_categories = list(saved_categories)
                if selected_expense[4] not in existing_categories:
                    existing_categories.append(selected_expense[4])
                update_category_choice = st.selectbox(
                    "Category",
                    [NEW_CATEGORY] + existing_categories,
                    index=existing_categories.index(selected_expense[4]) + 1,
                    key="update_category_choice",
                )
                new_custom_category = st.text_input(
                    "New category (when creating one)",
                    max_chars=40,
                    key="update_custom_category",
                )
                update_submitted = st.form_submit_button(
                    "Save changes", type="primary"
                )
            if update_submitted:
                new_category = (
                    new_custom_category.strip()
                    if update_category_choice == NEW_CATEGORY
                    else update_category_choice
                )
                if not expense_is_valid(new_amount, new_date, new_reason, new_category):
                    st.error(
                        "Check the amount, date, category (1–40 characters), "
                        "and reason (up to 100 characters)."
                    )
                elif update_expense(
                    selected_expense[0],
                    new_amount,
                    new_date.strftime("%Y-%m-%d"),
                    new_reason,
                    new_category,
                ):
                    st.toast("Expense updated successfully.", icon="✅")
                    st.rerun()
                else:
                    st.error("Could not update the expense. Refresh and try again.")

    with delete_tab:
        if not expenses:
            st.info("There are no expenses to delete.")
        else:
            delete_options = {
                f"{row[2]} · {row[4]} · {money(row[1])} · {row[3] or 'No description'}": row[0]
                for row in expenses
            }
            selected_delete_label = st.selectbox(
                "Choose an expense",
                list(delete_options),
                key="delete_expense_select",
            )
            confirm_delete = st.checkbox(
                "I understand this permanently deletes the selected expense.",
                key="confirm_delete",
            )
            if st.button(
                "Delete expense",
                type="primary",
                disabled=not confirm_delete,
                key="delete_expense_button",
            ):
                if delete_expense(delete_options[selected_delete_label]):
                    st.toast("Expense deleted.", icon="🗑️")
                    st.rerun()
                else:
                    st.error("Could not delete the expense. Refresh and try again.")
