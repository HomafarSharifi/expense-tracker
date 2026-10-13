import streamlit as st
import pandas as pd
from datetime import date
from expenses import (
    add_expense,
    get_expenses,
    get_total_spending,
    get_spending_by_category,
    get_monthly_spending,
    update_expense,
    delete_expense,
    get_spending_by_date_range
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
overview_tab, analytics_tab, manage_tab = st.tabs([
    "Overview",
    "Analytics",
    "Manage Expenses"
])

# Load data
try:
    expenses = get_expenses()
    total_spending = get_total_spending()
    categories = get_spending_by_category()
except Exception:
    st.error(
        "Unable to load expense data. "
        "Please check the database and try again."
    )
    st.stop()


# Overview tab
with overview_tab:
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
    
    pass


# Analytics tab
with analytics_tab:
    
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


    # Date-range analysis
    st.header("Spending by Date Range")

    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input(
            "Start date",
            value=date.today().replace(day=1),
            key="filter_start_date"
        )

    with col2:
        end_date = st.date_input(
            "End date",
            value=date.today(),
            key="filter_end_date"
        )

    if start_date > end_date:
        st.warning("Start date cannot be after end date.")
    else:
        # Filter expense records for the selected period
        filtered_expenses = [
            row for row in expenses
            if start_date <= row[2] <= end_date
        ]

        # Calculate total spending for the selected period
        filtered_total = sum(
            (row[1] for row in filtered_expenses),
            start=0
        )

        st.metric(
            "Spending in Selected Period",
            f"{filtered_total:,.2f}"
        )

        st.subheader("Expenses in Selected Period")

        if filtered_expenses:
            filtered_data = [
                {
                    "ID": row[0],
                    "Amount": float(row[1]),
                    "Date": row[2],
                    "Reason": row[3] or "",
                    "Category": row[4]
                }
                for row in filtered_expenses
            ]

            st.dataframe(
                filtered_data,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No expenses found in this date range.")

    # Daily spending chart
    daily_results = get_spending_by_date_range(
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d")
    )

    if daily_results:
        daily_data = [
            {
                "Date": row[0],
                "Daily Spending": float(row[1] or 0)
            }
            for row in daily_results
        ]

        daily_df = pd.DataFrame(daily_data)
        st.subheader("Daily Spending Trend")
        st.line_chart(
            daily_df,
            x="Date",
            y="Daily Spending"
        )
    else:
        st.info("No daily spending data available for this period.")

    pass


# Manage Expenses tab
with manage_tab:
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
            success = add_expense(
                amount,
                expense_date.strftime("%Y-%m-%d"),
                reason,
                category
            )
    
            if success:
                st.success("Expense added successfully!")
                st.rerun()
            else:
                st.error("Failed to add expense. Check the terminal for details.")


    # Update expense
    st.header("Manage Expenses")

    st.subheader("Update Expense")

    if expenses:
        expense_options = {
            f"ID {row[0]} — {row[3] or 'No description'} ({row[1]})": row
            for row in expenses
        }

        selected_label = st.selectbox(
            "Select an expense to update",
            options=list(expense_options.keys()),
            key="update_expense_select"
        )

        selected_expense = expense_options[selected_label]

        with st.form("update_expense_form"):
            new_amount = st.number_input(
                "Amount",
                min_value=0.01,
                value=float(selected_expense[1]),
                step=1.0,
                format="%.2f",
                key="update_amount"
            )

            new_date = st.date_input(
                "Date",
                value=selected_expense[2],
                key="update_date"
            )

            new_reason = st.text_input(
                "Reason",
                value=selected_expense[3] or "",
                max_chars=100,
                key="update_reason"
            )

            categories_list = [
                "FOOD",
                "TRANSPORT",
                "EDUCATION",
                "ENTERTAINMENT",
                "OTHER"
            ]

            current_category = selected_expense[4]
            category_index = (
                categories_list.index(current_category)
                if current_category in categories_list
                else 0
            )

            new_category = st.selectbox(
                "Category",
                categories_list,
                index=category_index,
                key="update_category"
            )

            update_submitted = st.form_submit_button("Save Changes")


        if update_submitted:
            success = update_expense(
                selected_expense[0],
                new_amount,
                new_date.strftime("%Y-%m-%d"),
                new_reason,
                new_category
            )

            if success:
                st.success("Expense updated successfully!")
                st.rerun()
            else:
                st.error("Failed to update expense. Check the terminal for details.")
    else:
        st.info("Add an expense before trying to update one.")
    
    # Delete expense
    st.subheader("Delete Expense")

    if expenses:
        delete_options = {
            f"ID {row[0]} — {row[3] or 'No description'} ({row[1]})": row[0]
            for row in expenses
        }

        selected_delete_label = st.selectbox(
            "Select an expense to delete",
            options=list(delete_options.keys()),
            key="delete_expense_select"
        )

        confirm_delete = st.checkbox(
            "I confirm that I want to permanently delete this expense.",
            key="confirm_delete"
        )


        if st.button("Delete Selected Expense", type="primary"):
            if confirm_delete:
                success = delete_expense(
                    delete_options[selected_delete_label]
                )

                if success:
                    st.success("Expense deleted successfully.")
                    st.rerun()
                else:
                    st.error("Failed to delete expense. Check the terminal for details.")
            else:
                st.warning("Please confirm before deleting.")
    else:
        st.info("There are no expenses to delete.")
    pass