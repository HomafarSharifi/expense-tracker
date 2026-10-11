import streamlit as st
import pandas as pd
from expenses import (
    add_expense,
    get_expenses,
    get_total_spending,
    get_spending_by_category,
    get_monthly_spending
)

# Page configuration
st.set_page_config(
    page_title="Expense Tracker",
    page_icon="💰",
    layout="wide"
)

# Page title
st.title("Personal Expense Tracker")

# Introduction
st.write("Track your expenses and understand your spending habits.")

# Sidebar
st.sidebar.title("Navigation")
st.sidebar.write("Choose a section to get started.")

# First section
st.header("Dashboard")

# Load data from the existing project functions
expenses = get_expenses()
total_result = get_total_spending()
categories = get_spending_by_category()

# Handle the total returned by the database function
total_spending = 0

if total_result and total_result[0] is not None:
    total_spending = total_result[0]

# Dashboard summary
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="Total Spending",
        value=f"{total_spending:,.2f}"
    )

with col2:
    st.metric(
        label="Number of Expenses",
        value=len(expenses)
    )

with col3:
    st.metric(
        label="Spending Categories",
        value=len(categories)
    )

# Expense history
st.subheader("Expense History")

if expenses:
    expense_data = [
        {
            "ID": row[0],
            "Amount": float(row[1]),
            "Date": row[2],
            "Reason": row[3] or "",
            "Category": row[4]
        }
        for row in expenses
    ]

    st.dataframe(
        expense_data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Amount": st.column_config.NumberColumn(
                "Amount",
                format="%.2f"
            ),
            "Date": st.column_config.DateColumn(
                "Date",
                format="YYYY-MM-DD"
            )
        }
    )
else:
    st.info("No expenses found. Add your first expense to get started.")



# Spending analytics
st.header("Spending Analytics")

# Chart 1: Spending by category
st.subheader("Spending by Category")

if categories:
    category_data = [
        {
            "Category": row[0],
            "Total Spending": float(row[1] or 0)
        }
        for row in categories
    ]

    category_df = pd.DataFrame(category_data)

    st.bar_chart(
        category_df,
        x="Category",
        y="Total Spending"
    )
else:
    st.info("No category data available yet.")

# Chart 2: Monthly spending
st.subheader("Monthly Spending")

monthly_results = get_monthly_spending()

if monthly_results:
    monthly_data = [
        {
            "Month": str(row[0]),
            "Total Spending": float(row[1] or 0)
        }
        for row in monthly_results
    ]

    monthly_df = pd.DataFrame(monthly_data)

    st.bar_chart(
        monthly_df,
        x="Month",
        y="Total Spending"
    )
else:
    st.info("No monthly spending data available yet.")
    

# Add expense section
st.subheader("Add a New Expense")

with st.form("add_expense_form"):
    amount = st.number_input(
        "Amount",
        min_value=0.01,
        step=1.0,
        format="%.2f"
    )

    expense_date = st.date_input("Date")

    reason = st.text_input(
        "Reason",
        max_chars=100,
        placeholder="e.g. Lunch"
    )

    category = st.selectbox(
        "Category",
        [
            "FOOD",
            "TRANSPORT",
            "EDUCATION",
            "ENTERTAINMENT",
            "OTHER"
        ]
    )

    submitted = st.form_submit_button("Save Expense")

    if submitted:
        add_expense(
            amount,
            expense_date.strftime("%Y-%m-%d"),
            reason,
            category
        )

        st.success("Expense added successfully!")
        st.rerun()