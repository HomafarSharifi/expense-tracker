expense = {'amount': 200, 'date': '2026-10-7', 'reason': 'I was hungry', 'category': 'food'}

print(expense.get('amount', 'NULL'))
print(expense['category'])
print(list(expense.values()))