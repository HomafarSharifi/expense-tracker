"""Create README screenshots from fictional records in a throwaway local database."""

from datetime import date, timedelta
from pathlib import Path
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication

from expense_tracker.desktop import MainWindow
from expense_tracker.reports import configure_report_font
from expense_tracker.storage import ExpenseStore

TEMP = ROOT / ".test-tmp"
SCREENSHOTS = ROOT / "screenshots"


def month_start(months_ago: int) -> date:
    today = date.today()
    index = today.year * 12 + today.month - 1 - months_ago
    return date(index // 12, index % 12 + 1, 1)


def main():
    TEMP.mkdir(exist_ok=True); SCREENSHOTS.mkdir(exist_ok=True)
    database = TEMP / "readme-demo.sqlite3"
    for stale_file in (database, Path(str(database) + "-wal"), Path(str(database) + "-shm")):
        stale_file.unlink(missing_ok=True)
    store = ExpenseStore(database)
    examples = (("Groceries", 2350, "Market"), ("Transport", 640, "Taxi"),
                ("Home", 1800, "Electricity"), ("Health", 950, "Pharmacy"),
                ("Groceries", 720, "Bakery"), ("Education", 1200, "Books"),
                ("Utilities", 840, "Internet"), ("Home", 1550, "Gas"),
                ("Personal", 480, "Household supplies"), ("Giving", 600, "Donation"))
    for months_ago in range(6, -1, -1):
        start = month_start(months_ago)
        store.add_income(42000 + months_ago * 500, start, "Salary")
        if months_ago == 0:
            for index, (category, amount, description) in enumerate(examples):
                day = min(date.today().day, 2 + index * 3)
                store.add_expense(amount, start.replace(day=day), description, category)
        else:
            store.add_expense(9200 + months_ago * 630, start + timedelta(days=5), "Monthly essentials", "Household")
            store.add_expense(2100 + months_ago * 170, start + timedelta(days=12), "Local travel", "Transport")

    app = QApplication.instance() or QApplication([])
    configure_report_font()
    font_path = ROOT / "assets" / "fonts" / "Vazirmatn-Regular.ttf"
    if font_path.exists(): QFontDatabase.addApplicationFont(str(font_path))
    app.setFont(QFont("Segoe UI", 10))
    app.setStyleSheet("""
        QWidget { color: #17324d; font-size: 10pt; }
        QMainWindow, QWidget { background: #f5f8fb; }
        QTabWidget::pane { border: 1px solid #d8e2ea; border-radius: 8px; background: white; }
        QTabBar::tab { background: #e7eef4; padding: 10px 18px; margin: 3px; border-radius: 7px; }
        QTabBar::tab:selected { color: white; background: #176b72; }
        QLineEdit, QComboBox, QDateEdit, QSpinBox, QTableWidget { background: white; border: 1px solid #c8d5df; border-radius: 5px; padding: 6px; }
        QPushButton { background: #176b72; color: white; padding: 8px 14px; border: 0; border-radius: 6px; }
        QPushButton#dangerButton { background: #b53b42; }
        QFrame#summaryCard { background: white; border: 1px solid #dce5eb; border-radius: 10px; }
        QLabel#summaryValue { font-size: 19pt; font-weight: 700; }
    """)
    window = MainWindow(database); window.resize(1420, 760); window.show(); app.processEvents()
    window.overview_size_picker.setCurrentText("10"); app.processEvents()
    window.grab().save(str(SCREENSHOTS / "overview.png"))
    window.tabs.setCurrentIndex(3); window.chart_mode.setCurrentIndex(1); app.processEvents()
    window.grab().save(str(SCREENSHOTS / "analytics.png"))
    window.language_picker.setCurrentText("Dari")
    window.calendar_picker.setCurrentIndex(1); app.processEvents()
    window.grab().save(str(SCREENSHOTS / "dari-analytics.png"))
    window.tabs.setCurrentIndex(0); app.processEvents()
    window.grab().save(str(SCREENSHOTS / "dari-overview.png"))
    window.close(); app.processEvents()
    print(f"Created fictional-data screenshots in {SCREENSHOTS}")


if __name__ == "__main__":
    main()
