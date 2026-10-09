from expenses import add_expense, update_expense, delete_expense, get_expenses, get_spending_by_category, get_total_spending, get_spending_over_time
from visualizations import plot_spending_over_time, plot_spending_by_category

while True:
    choice = int(input("1. Add expense \n2. View expenses \n3. Update expense \n4. Delete expense \n5. Total spending by category \n6. Total spending \n7. Daily spending \n8. Daily Spending Over Time Chart\n9. Spending by Category Chart \n10. Exit\n"))

    if choice == 1:
        amount = float(input("Enter amount: "))
        date = input("Enter date (YYYY-MM-DD): ")
        reason = input("Enter reason: ")
        category = input("Enter category: ")
        add_expense(amount, date, reason, category)

    elif choice == 2:
        expenses = get_expenses()
        print(expenses)

    elif choice == 3:
        amount = float(input("Enter amount: "))
        date = input("Enter date (YYYY-MM-DD): ")
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
        print(get_spending_over_time())

    elif choice == 8:
        plot_spending_over_time()

    elif choice == 9:
        plot_spending_by_category()

    elif choice == 10:
        print('Bye')
        break
    else:
        print('Invalid Option!\n')
        continue