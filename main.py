from expenses import add_expense, update_expense, delete_expense, get_expenses, get_spending_by_category, get_total_spending, get_spending_over_time
from visualizations import plot_spending_over_time, plot_spending_by_category, plot_monthly_spending, plot_spending_by_date_range
from datetime import datetime

def get_valid_amount():
    while True:
        try:
            value = float(input("Enter the amount: "))
            if value<=0:
                print('The value should be greater than zero!!')
                continue
            return value
        except ValueError:
            print("Please enter a valid number.")
            continue

def get_valid_date():
    while True:
        try:
            date_text = input("Enter the date in (YYYY-MM-DD) format: ")
            datetime.strptime(date_text, "%Y-%m-%d")
            return date_text
        except ValueError:
            print("Invalid date. Please use YYYY-MM-DD")
            continue

while True:
    try:
        choice = int(input(
        "1. Add expense\n"
        "2. View expenses\n"
        "3. Update expense\n"
        "4. Delete expense\n"
        "5. Total spending by category\n"
        "6. Total spending\n"
        "7. Spending by Date Range\n"
        "8. Daily Spending Over Time Chart\n"
        "9. Spending by Category Chart\n"
        "10. Monthly Spending\n"
        "11. Exit\n"
        "Enter your choice: "
        ))
    except ValueError:
        print("Please enter a valid menu number.")
        continue

    if choice == 1:
        amount = get_valid_amount()
        date = get_valid_date()
        reason = input("Enter reason: ")
        category = input("Enter category: ")
        add_expense(amount, date, reason, category)
    elif choice == 2:
        expenses = get_expenses()
        print(expenses)
    elif choice == 3:
        amount = get_valid_amount()
        date = get_valid_date()
        reason = input("Enter reason: ")
        category = input("Enter category: ")
        id_expense = input("In which ID do you wanna make change: ")
        update_expense(id_expense, amount, date, reason, category)
    elif choice == 4:
        id_expense = input("which ID do you wanna remove: ")
        delete_expense(id_expense)
    elif choice == 5:
        print(get_spending_by_category())
    elif choice == 6:
        print(get_total_spending())
    elif choice == 7:
        start = get_valid_date()
        end = get_valid_date()
        if start > end:
            print("Start date must not be after end date.")
            continue
        else:
            plot_spending_by_date_range(start, end)
    elif choice == 8:
        plot_spending_over_time()
    elif choice == 9:
        plot_spending_by_category()
    elif choice == 10:
        plot_monthly_spending()
    elif choice == 11:
        print('Bye')
        break
    else:
        print('Invalid Option!\n')
        continue