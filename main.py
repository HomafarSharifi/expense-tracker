from expenses import add_expense, update_expense, delete_expense, get_expenses

while True:
    choice = int(input("\n1. Add expense\n2. View expenses\n3. Update expense\n4. Delete expense\n5. Exit\n"))

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
        print('Bye')
        break
    else:
        print('Invalid Option!\n')
        continue