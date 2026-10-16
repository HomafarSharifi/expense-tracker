# Personal Expense Tracker

A Streamlit app for recording expenses, managing categories, and exploring spending trends stored in MySQL or MariaDB.

## Features

- Add, update, and delete expenses with clear confirmation and feedback
- Quick add from the sidebar while viewing any page
- Reuse saved categories or create a new one
- Search and filter expense history
- Review color-coded category spending, stacked monthly trends, and daily trends for a selected date range
- Set a display currency with the EXPENSE_CURRENCY environment variable

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

4. Create the database and table. For a fresh database, import expenses.sql with your MySQL/MariaDB client. That file includes example rows; remove its INSERT section if you want an empty database. Or create the schema manually:

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

5. Configure the connection in PowerShell before launching the app:

   ~~~powershell
   $env:EXPENSE_DB_HOST = "localhost"
   $env:EXPENSE_DB_PORT = "3306"
   $env:EXPENSE_DB_USER = "expense_app"
   $env:EXPENSE_DB_PASSWORD = "your-local-password"
   $env:EXPENSE_DB_NAME = "expense_tracker"
   $env:EXPENSE_CURRENCY = "USD"
   ~~~

   The default connection is localhost:3306, user root, and database expense_tracker for local compatibility. Set a password in EXPENSE_DB_PASSWORD and prefer a dedicated database account. Never commit passwords or real expense data.

6. Start the web app:

   ~~~powershell
   streamlit run app.py
   ~~~

   The optional command-line interface can be started with python main.py.

## Screenshots for GitHub

For a polished project page, capture the Overview, Analytics, and Manage expenses tabs with sample data. Save them in a screenshots/ folder and embed them here with relative image paths. Use fictional sample records and hide connection details.

## Ready-to-use checklist

- [ ] Install Python dependencies and start MySQL/MariaDB.
- [ ] Create the database and expenses table.
- [ ] Set the database environment variables.
- [ ] Run the app and verify add, update, delete, filters, and analytics.
- [ ] Capture screenshots with fictional data before publishing.
