# Personal Expense Tracker

A Streamlit app for recording expenses, managing categories, and exploring spending trends stored in MySQL or MariaDB.

## Features

- Add, update, and delete expenses with clear confirmation and feedback
- Record monthly income from multiple sources and see the month's income, spending, and remaining balance
- Quick add from the sidebar while viewing any page
- Reuse saved categories or create a new one
- Search and filter expense history
- Switch monthly charts between total spending, category breakdown, and income versus spending; review color-coded category and daily trends
- Set a display currency with the EXPENSE_CURRENCY environment variable
- Switch the interface between English and Dari; Dari mode uses a right-to-left layout
- Use the Afghan Solar Hijri calendar throughout Dari mode, with Afghan month names

## Requirements

- Python 3.10 or newer
- MySQL 8 or MariaDB 10.4 or newer
- A database user permitted to read, insert, update, and delete records in expense_tracker
- Python packages: streamlit, pandas, mysql-connector-python, and matplotlib (matplotlib is needed for the optional command-line charts)

## Setup

1. Clone or copy this repository and open PowerShell in the project folder.
2. Create and activate a virtual environment:

   ~~~powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   ~~~

3. Install the packages listed above directly from this README:

   ~~~powershell
   python -m pip install "streamlit>=1.30" "pandas>=2.0" "mysql-connector-python>=8.0" "matplotlib>=3.7"
   ~~~

4. Create the database and expense table. For a fresh database, import expenses.sql with your MySQL/MariaDB client. That file includes example rows; remove its INSERT section if you want an empty database. Or create the schema manually:

   ~~~sql
   CREATE DATABASE expense_tracker CHARACTER SET utf8mb4;
   USE expense_tracker;
   CREATE TABLE expenses (
       id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
       amount DECIMAL(10, 2) NOT NULL,
       date DATE NOT NULL,
       reason VARCHAR(100),
       category VARCHAR(40) NOT NULL
   );
   ~~~

5. Create the monthly income table by running `income.sql` while connected to `expense_tracker`. This is safe for existing installations: it adds the income table and leaves all expense records untouched. For example, with the MySQL command-line client:

   ~~~powershell
   Get-Content .\income.sql | mysql -u expense_app -p expense_tracker
   ~~~

6. Configure the connection in PowerShell before launching the app:

   ~~~powershell
   $env:EXPENSE_DB_HOST = "localhost"
   $env:EXPENSE_DB_PORT = "3306"
   $env:EXPENSE_DB_USER = "expense_app"
   $env:EXPENSE_DB_PASSWORD = "your-local-password"
   $env:EXPENSE_DB_NAME = "expense_tracker"
   $env:EXPENSE_CURRENCY = "AFN"
   ~~~

   The default connection is localhost:3306, user root, and database expense_tracker for local compatibility. Set a password in EXPENSE_DB_PASSWORD and prefer a dedicated database account. Never commit passwords or real expense data.

7. Start the web app:

   ~~~powershell
   streamlit run app.py
   ~~~

   The optional command-line interface can be started with python main.py.

## Monthly income and balance

Choose a month on the Overview tab, then add salary or any other income source in the Income tab. Add separate entries for multiple sources; the app sums them automatically. The remaining amount is monthly income minus expenses recorded during that calendar month. If no income is recorded, the app treats income as zero and prompts you to add it. The Analytics tab lets you switch the monthly chart between total spending, spending by category, and income-versus-spending. Months are shown in chronological order.

## Language

Use the **Language** selector in the sidebar to switch between English and Dari (دری). The choice stays active during the current app session. Dari mode translates the app controls, guidance, chart and table labels, standard category names, notifications, and empty states, and aligns the interface right-to-left. Dates in Dari mode use the Afghan Solar Hijri calendar and Afghan month names: حمل، ثور، جوزا، سرطان، اسد، سنبله، میزان، عقرب، قوس، جدی، دلو، حوت. Date entry, expense history, date-range filters, income months, monthly summaries, and analytics use those calendar months. The app converts selected dates to Gregorian dates for storage, so existing expense records and database schemas need no migration. English mode continues to use Gregorian dates. It uses the Vazir font from jsDelivr, with local sans-serif fallbacks if the font CDN is unavailable. User-created category names, income sources, and expense descriptions remain as entered.

## Screenshots for GitHub

For a polished project page, capture the Overview, Analytics, and Manage expenses tabs with sample data. Save them in a screenshots/ folder and embed them here with relative image paths. Use fictional sample records and hide connection details.

## Ready-to-use checklist

- [ ] Install Python dependencies and start MySQL/MariaDB.
- [ ] Create the database and expenses table, then run `income.sql`.
- [ ] Set the database environment variables.
- [ ] Run the app and verify income, monthly balance, expense add/update/delete, filters, and analytics.
- [ ] Capture screenshots with fictional data before publishing.
