import matplotlib.pyplot as plt
from expenses import get_spending_over_time, get_spending_by_category, get_monthly_spending, get_spending_by_date_range

def plot_spending_over_time():
    rows = get_spending_over_time()
    if not rows:
        print("No expense data available.")
        return
    
    dates = [row[0] for row in rows]
    amounts = [float(row[1]) for row in rows]
    plt.plot(dates, amounts, marker="o")
    plt.title('Daily Spending Over Time')
    plt.xlabel("Date")
    plt.ylabel("Amount Spent")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def plot_spending_by_category():
    rows = get_spending_by_category()
    if not rows:
        print("No expense data available.")
        return

    categories = [row[0] for row in rows]
    amounts = [float(row[1]) for row in rows]
    plt.figure(figsize=(8, 5))
    plt.bar(categories, amounts)
    plt.title("Spending by Category")
    plt.xlabel("Category")
    plt.ylabel("Total Amount")
    plt.tight_layout()
    plt.show()

def plot_monthly_spending():
    rows = get_monthly_spending()
    if not rows:
        print("No expense data available.")
        return
    months = [row[0] for row in rows]
    amounts = [float(row[1]) for row in rows]
    plt.figure(figsize=(8, 5))
    plt.bar(months, amounts)
    plt.title("Monthly Spending")
    plt.xlabel("Months")
    plt.ylabel("Total Amount")
    plt.tight_layout()
    plt.show()

def plot_spending_by_date_range(start_date, end_date):
    rows = get_spending_by_date_range(start_date, end_date)
    if not rows:
        print("No expense data available.")
        return
    dates = [row[0] for row in rows]
    amounts = [float(row[1]) for row in rows]
    plt.figure(figsize=(8, 5))
    plt.plot(dates, amounts, marker="o")
    plt.title("Spending by Date Range")
    plt.xlabel("Dates")
    plt.ylabel("Total Amount")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()