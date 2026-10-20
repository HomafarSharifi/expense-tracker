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
- Independently choose Gregorian or Afghan Solar Hijri dates in either language
- Use the computer's current system date and time; enable automatic internet time synchronization in the operating system to keep its clock accurate

## Requirements

- Python 3.10 or newer
- MySQL 8 or MariaDB 10.4 or newer
- A database user permitted to read, insert, update, and delete records in expense_tracker
- Python packages: streamlit, pandas, mysql-connector-python, and matplotlib (matplotlib is needed for the optional command-line charts)

## First-time setup on Windows

1. Clone or copy this repository and open PowerShell in the project folder.
2. Install MySQL or MariaDB and start its Windows service (open **Services** from the Start menu if it is not running). Keep the database service running while using the tracker.
3. Create and activate a virtual environment:

   ~~~powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   ~~~

4. Install the packages listed above directly from this README:

   ~~~powershell
   python -m pip install "streamlit>=1.30" "pandas>=2.0" "mysql-connector-python>=8.0" "matplotlib>=3.7"
   ~~~

5. Create the database and expense table. For a fresh install using the MySQL command-line client, run these commands from the project folder. The sample SQL inserts demo expenses; remove the INSERT section from a copy if you want an empty table:

   ~~~powershell
   mysql -u root -p -e "CREATE DATABASE expense_tracker CHARACTER SET utf8mb4;"
   Get-Content .\expenses.sql | mysql -u root -p expense_tracker
   ~~~

   Or create the schema manually:

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

6. Create the monthly income table by running `income.sql` while connected to `expense_tracker`. This is safe for existing installations: it adds the income table and leaves all expense records untouched. Run schema setup with a database administrator account:

   ~~~powershell
   Get-Content .\income.sql | mysql -u root -p expense_tracker
   ~~~

7. Create a dedicated account for the app after both tables exist. Run this as a database administrator and replace the example password:

   ~~~sql
   CREATE USER 'expense_app'@'localhost' IDENTIFIED BY 'choose-a-strong-local-password';
   GRANT SELECT, INSERT, UPDATE, DELETE ON expense_tracker.* TO 'expense_app'@'localhost';
   ~~~

8. Copy the local secrets template and enter the dedicated account password in the ignored local file:

   ~~~powershell
   Copy-Item .\.streamlit\secrets.toml.example .\.streamlit\secrets.toml
   notepad .\.streamlit\secrets.toml
   ~~~

   Set `EXPENSE_DB_HOST`, `EXPENSE_DB_PORT`, `EXPENSE_DB_USER`, `EXPENSE_DB_PASSWORD`, and `EXPENSE_DB_NAME` in that file. Environment variables with the same names take precedence. The app defaults to localhost and the `expense_tracker` database for compatibility, but a dedicated database account with a password is recommended. `.streamlit/secrets.toml` is ignored by Git; never commit passwords or real expense data.

9. Start the web app:

   ~~~powershell
   streamlit run app.py
   ~~~

   Keep that terminal open while using the app, then open the local address Streamlit prints. On later days, open PowerShell in the project folder, activate `.venv`, and run `streamlit run app.py`. The optional command-line interface can be started with `python main.py`.

## Daily use

1. Choose English or Dari in the sidebar, then choose Gregorian or Afghan Solar Hijri under **Calendar**. Both calendar types work in either language; the database always stores Gregorian dates.
2. Use **Quick add** for a one-line expense, or **Manage expenses** for a detailed entry. Pick a saved category; choose the final “create new category” option only when needed.
3. Add salary or other income in **Income** for the month you selected. The Overview shows income, spending, and the remaining balance for that month.
4. Use **Find expenses** for a simple category filter or description search. Use Analytics for monthly comparisons or a date range.
5. Review the selected expense and confirmation checkbox before deleting it. The app reports successful saves and deletions.

## Back up and restore your data

From the project folder with `.venv` active, create a backup before updates or database changes:

~~~powershell
python data_backup.py backup
~~~

The command saves both expenses and income as a UTF-8 JSON file in the ignored `backups/` folder. The JSON file is not encrypted and contains personal financial data. Copy it to a separate, private location (for example, an encrypted external drive or a private backup service); never commit or publicly upload it. The app does not send backups anywhere automatically.

To restore, first create an empty `expenses` table and an empty `monthly_income` table in the target database, configure the app to connect to it, and run:

~~~powershell
python data_backup.py restore .\backups\expense-tracker-YYYYMMDD-HHMMSS.json
~~~

Restore validates the backup and refuses to run if either table already has records; this prevents an accidental overwrite. For a fresh restore database, create the tables using the schema in `expenses.sql` and `income.sql`. If you import `expenses.sql`, remove its sample `INSERT` section first so the target table is empty. To update an existing installation, back it up first, then apply `income.sql` only if the monthly income table is missing. The app code itself needs no schema migration for the Dari calendar.

## Monthly income and balance

Choose a month on the Overview tab, then add salary or any other income source in the Income tab. Add separate entries for multiple sources; the app sums them automatically. The remaining amount is monthly income minus expenses recorded during that calendar month. If no income is recorded, the app treats income as zero and prompts you to add it. The Analytics tab lets you switch the monthly chart between total spending, spending by category, and income-versus-spending. Months are shown in chronological order.

## Advanced settings

Open **Advanced settings** in the sidebar to review the active currency and non-secret database connection details, see the connection status, and create a local JSON backup. Passwords are never displayed. The backup contains private, unencrypted financial data; keep it somewhere secure and outside Git. Configuration examples in the panel show where database settings belong and how to change the display currency. The UI stacks cards and controls on narrow screens and keeps tabs horizontally scrollable on phones.

## Language

Use the **Language** selector in the sidebar to switch between English and Dari (دری), then choose a calendar directly below it. Both languages offer Gregorian and Afghan Solar Hijri dates, using the same year/month/day selectors for full dates. Overview and monthly income intentionally ask only for a month, so those controls omit the day. Solar Hijri uses Afghan month names: حمل، ثور، جوزا، سرطان، اسد، سنبله، میزان، عقرب، قوس، جدی، دلو، حوت. Date entry, expense history, date-range filters, income months, monthly summaries, and analytics follow the selected calendar. Switching calendars carries selected dates into the equivalent date in the other calendar. The app converts selected dates to Gregorian dates for storage, so existing expense records and database schemas need no migration. Dari keeps the right-to-left layout and Vazir font. The displayed clock and default dates come from the computer running the app; enable automatic time synchronization in that computer's operating system to keep it aligned with internet time. User-created category names, income sources, and expense descriptions remain as entered.

## Screenshots for GitHub

For a polished project page, capture the Overview, Analytics, and Manage expenses tabs with sample data. Save them in a screenshots/ folder and embed them here with relative image paths. Use fictional sample records and hide connection details.

## Ready-to-use checklist

- [ ] Install Python dependencies and start MySQL/MariaDB.
- [ ] Create the database and tables, then run `income.sql`.
- [ ] Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and set a password.
- [ ] Start the app and confirm expenses, income, monthly balance, edits, deletions, filters, charts, and both calendars.
- [ ] Create a backup and keep a copy in a private location outside the project folder.
- [ ] Capture screenshots with fictional data before publishing.
