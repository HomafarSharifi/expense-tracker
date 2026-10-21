"""PySide6 desktop application. Importing the CLI never requires the GUI toolkit."""

from __future__ import annotations

import csv
from io import BytesIO
from datetime import date
from decimal import Decimal
from pathlib import Path
import sqlite3
import sys

from jalali_calendar import AFGHAN_MONTHS, calendar_date_to_gregorian, format_jalali_date, to_jalali

from PySide6.QtCore import QDate, Qt, QUrl
from PySide6.QtGui import QDesktopServices, QFont, QFontDatabase, QIcon, QImage, QTextDocument
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import (
    QApplication, QComboBox, QDateEdit, QFileDialog, QFormLayout, QFrame,
    QGridLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMainWindow,
    QMessageBox, QPushButton, QSpinBox, QTabWidget, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from .reports import _safe_cell, configure_report_font, export_figure_pdf, export_table_pdf, html_table, shape_rtl
from .storage import ExpenseStore, default_database_path
from .diagnostics import write_debug_log
from database_errors import database_error_help

TEXT = {
    "English": {
        "title": "Expense Tracker", "overview": "Overview", "expenses": "Expenses",
        "income": "Income", "analytics": "Analytics", "settings": "Settings",
        "language": "Language", "calendar": "Calendar", "month": "Month",
        "income_total": "Income", "spending": "Spending", "remaining": "Remaining",
        "recent": "Recently added", "oldest": "Oldest first", "highest": "Highest amount",
        "lowest": "Lowest amount", "rows": "Rows per page", "previous": "Previous",
        "next": "Next", "page": "Page", "date": "Date", "amount": "Amount (AFN)",
        "category": "Category", "description": "Description", "source": "Source",
        "search": "Search", "add": "Add", "save": "Save changes", "delete": "Delete",
        "new_expense": "New expense", "new_income": "New income", "backup": "Create backup",
        "restore": "Restore backup", "export_csv": "Share / export CSV", "export_pdf": "Save PDF",
        "print": "Print", "saved": "Saved successfully.", "confirm_delete": "Delete the selected record?",
        "empty": "No records yet. Add your first one to get started.", "choose_record": "Select a record first.",
        "data_file": "Private local data file", "safe_note": "Your records stay on this computer. The app sends no data online.",
        "report": "Monthly spending", "select_calendar": "Calendar type",
        "clear": "Clear form", "delete_income": "Delete selected income", "amount_label": "Amount (AFN)",
        "date_label": "Date", "category_label": "Category", "description_label": "Description",
        "month_label": "Month", "language_label": "Language", "calendar_label": "Calendar",
        "spending_chart": "Spending by month", "comparison_chart": "Income vs spending", "category_chart": "By category",
        "graph_pdf": "Share graph as PDF", "print_graph": "Print graph", "income_series": "Income", "spending_series": "Spending",
        "gregorian_calendar": "Gregorian", "solar_calendar": "Afghan Solar Hijri",
        "sort_by": "Sort by", "page_size": "Rows per page", "print_page": "Print this page",
    },
    "Dari": {
        "title": "مدیریت مصارف", "overview": "نمای کلی", "expenses": "مصارف",
        "income": "درآمد", "analytics": "گزارش‌ها", "settings": "تنظیمات",
        "language": "زبان", "calendar": "تقویم", "month": "ماه",
        "income_total": "درآمد", "spending": "مصارف", "remaining": "باقی‌مانده",
        "recent": "تازه‌ترین", "oldest": "قدیمی‌ترین", "highest": "بیشترین مبلغ",
        "lowest": "کمترین مبلغ", "rows": "ردیف در هر صفحه", "previous": "قبلی",
        "next": "بعدی", "page": "صفحه", "date": "تاریخ", "amount": "مبلغ (AFN)",
        "category": "دسته‌بندی", "description": "توضیحات", "source": "منبع",
        "search": "جستجو", "add": "افزودن", "save": "ذخیره تغییرات", "delete": "حذف",
        "new_expense": "مصرف جدید", "new_income": "درآمد جدید", "backup": "ایجاد پشتیبان",
        "restore": "بازیابی پشتیبان", "export_csv": "اشتراک / خروجی CSV", "export_pdf": "ذخیره PDF",
        "print": "چاپ", "saved": "با موفقیت ذخیره شد.", "confirm_delete": "این مورد حذف شود؟",
        "empty": "هنوز موردی ثبت نشده است. برای شروع مورد نخست را اضافه کنید.", "choose_record": "نخست یک مورد را انتخاب کنید.",
        "data_file": "فایل خصوصی داده‌ها", "safe_note": "اطلاعات شما در همین کمپیوتر می‌ماند و آنلاین فرستاده نمی‌شود.",
        "report": "مصارف ماهانه", "select_calendar": "نوع تقویم",
        "clear": "پاک‌کردن", "delete_income": "حذف درآمد انتخاب‌شده", "amount_label": "مبلغ (AFN)",
        "date_label": "تاریخ", "category_label": "دسته‌بندی", "description_label": "توضیحات",
        "month_label": "ماه", "language_label": "زبان", "calendar_label": "تقویم",
        "spending_chart": "مصارف ماهانه", "comparison_chart": "درآمد و مصارف", "category_chart": "بر اساس دسته‌بندی",
        "graph_pdf": "اشتراک نمودار به‌صورت PDF", "print_graph": "چاپ نمودار", "income_series": "درآمد", "spending_series": "مصارف",
        "gregorian_calendar": "میلادی", "solar_calendar": "هجری شمسی افغانستان",
        "sort_by": "مرتب‌سازی", "page_size": "ردیف در هر صفحه", "print_page": "چاپ این صفحه",
    },
}


def amount_text(value: Decimal) -> str:
    return f"{value:,.2f} AFN"


class CalendarDateInput(QWidget):
    """Date entry that supports Gregorian dates and Afghan Solar Hijri dates."""

    def __init__(self, get_calendar, parent=None):
        super().__init__(parent)
        self.get_calendar = get_calendar
        self.gregorian = QDateEdit(QDate.currentDate())
        self.gregorian.setCalendarPopup(True)
        self.gregorian.setDisplayFormat("yyyy-MM-dd")
        self.year = QComboBox(); self.month = QComboBox(); self.day = QComboBox()
        current = to_jalali(date.today())
        self.year.addItems([str(year) for year in range(max(1300, current.year - 60), current.year + 41)])
        self.year.setCurrentText(str(current.year))
        self.month.addItems(list(AFGHAN_MONTHS)); self.month.setCurrentIndex(current.month - 1)
        self.year.currentIndexChanged.connect(self._refresh_days)
        self.month.currentIndexChanged.connect(self._refresh_days)
        self._refresh_days()
        self.row = QHBoxLayout(self); self.row.setContentsMargins(0, 0, 0, 0)
        for widget in (self.gregorian, self.year, self.month, self.day): self.row.addWidget(widget)
        self.set_calendar_visibility()

    def _refresh_days(self):
        old = self.day.currentText() if self.day.count() else "1"
        year, month = int(self.year.currentText()), self.month.currentIndex() + 1
        first = calendar_date_to_gregorian(year, month, 1, "Afghan Solar Hijri")
        if month == 12:
            from jalali_calendar import to_gregorian
            next_first = to_gregorian(year + 1, 1, 1)
        else:
            from jalali_calendar import to_gregorian
            next_first = to_gregorian(year, month + 1, 1)
        count = (next_first - first).days
        self.day.blockSignals(True); self.day.clear(); self.day.addItems([str(item) for item in range(1, count + 1)])
        self.day.setCurrentText(str(min(int(old), count))); self.day.blockSignals(False)

    def set_calendar_visibility(self):
        solar = self.get_calendar() == "Afghan Solar Hijri"
        self.gregorian.setVisible(not solar)
        for widget in (self.year, self.month, self.day): widget.setVisible(solar)

    def value(self) -> date:
        if self.get_calendar() == "Gregorian":
            return self.gregorian.date().toPython()
        return calendar_date_to_gregorian(self.year.currentText(), self.month.currentIndex() + 1,
                                          self.day.currentText(), "Afghan Solar Hijri")

    def set_value(self, value: date):
        if self.get_calendar() == "Gregorian":
            self.gregorian.setDate(QDate(value.year, value.month, value.day))
        else:
            solar = to_jalali(value)
            self.year.setCurrentText(str(solar.year)); self.month.setCurrentIndex(solar.month - 1)
            self.day.setCurrentText(str(solar.day))


class CalendarMonthInput(QWidget):
    """Month picker with Gregorian or Afghan Solar Hijri year and month controls."""

    def __init__(self, get_calendar, on_change=None, parent=None):
        super().__init__(parent)
        self.get_calendar, self.on_change = get_calendar, on_change
        current = to_jalali(date.today())
        self.gregorian = QDateEdit(QDate.currentDate()); self.gregorian.setCalendarPopup(True); self.gregorian.setDisplayFormat("yyyy-MM")
        self.year, self.month = QComboBox(), QComboBox()
        self.year.addItems([str(year) for year in range(max(1300, current.year - 60), current.year + 41)])
        self.year.setCurrentText(str(current.year)); self.month.addItems(list(AFGHAN_MONTHS)); self.month.setCurrentIndex(current.month - 1)
        self.row = QHBoxLayout(self); self.row.setContentsMargins(0, 0, 0, 0)
        for widget in (self.gregorian, self.year, self.month): self.row.addWidget(widget)
        self.gregorian.dateChanged.connect(self._changed); self.year.currentIndexChanged.connect(self._changed); self.month.currentIndexChanged.connect(self._changed)
        self.set_calendar_visibility()

    def set_calendar_visibility(self):
        solar = self.get_calendar() == "Afghan Solar Hijri"
        self.gregorian.setVisible(not solar); self.year.setVisible(solar); self.month.setVisible(solar)

    def value(self) -> date:
        if self.get_calendar() == "Gregorian":
            selected = self.gregorian.date().toPython()
            return selected.replace(day=1)
        return calendar_date_to_gregorian(self.year.currentText(), self.month.currentIndex() + 1, 1, "Afghan Solar Hijri")

    def bounds(self) -> tuple[date, date]:
        start = self.value()
        if self.get_calendar() == "Afghan Solar Hijri":
            current = to_jalali(start)
            next_start = calendar_date_to_gregorian(current.year + (1 if current.month == 12 else 0),
                                                    1 if current.month == 12 else current.month + 1,
                                                    1, "Afghan Solar Hijri")
        else:
            next_start = date(start.year + (1 if start.month == 12 else 0), 1 if start.month == 12 else start.month + 1, 1)
        return start, date.fromordinal(next_start.toordinal() - 1)

    def set_value(self, value: date):
        if self.get_calendar() == "Gregorian":
            self.gregorian.setDate(QDate(value.year, value.month, 1))
        else:
            solar = to_jalali(value); self.year.setCurrentText(str(solar.year)); self.month.setCurrentIndex(solar.month - 1)

    def _changed(self, *_):
        if self.on_change: self.on_change()


class MainWindow(QMainWindow):
    def __init__(self, database_path: str | Path | None = None):
        super().__init__()
        self.store = ExpenseStore(database_path)
        self.language = self.store.get_preference("language", "English")
        self.calendar = self.store.get_preference("calendar", "Gregorian")
        if self.language not in TEXT: self.language = "English"
        if self.calendar not in {"Gregorian", "Afghan Solar Hijri"}: self.calendar = "Gregorian"
        self.page_size, self.overview_page, self.expense_page, self.income_page, self.month_page = 20, 1, 1, 1, 1
        self.overview_sort, self.expense_sort, self.income_sort, self.month_sort = "recent", "recent", "recent", "recent"
        self.selected_expense_id = None; self.selected_income_id = None
        self.control_labels = []
        self.setMinimumSize(900, 640); self.resize(1180, 800)
        self.tabs = QTabWidget(); self.setCentralWidget(self.tabs)
        self._build_overview(); self._build_expenses(); self._build_income(); self._build_analytics(); self._build_settings()
        self.refresh_all(); self.apply_language()

    def tr(self, key): return TEXT[self.language].get(key, key)

    def _build_overview(self):
        self.overview = QWidget(); layout = QVBoxLayout(self.overview)
        self.overview_heading = QLabel(); self.month_picker = CalendarMonthInput(lambda: self.calendar, self.refresh_overview)
        month_row = QHBoxLayout(); self.overview_month_label = QLabel(); month_row.addWidget(self.overview_month_label); month_row.addWidget(self.month_picker); month_row.addStretch()
        layout.addWidget(self.overview_heading); layout.addLayout(month_row)
        self.cards = []
        card_row = QHBoxLayout()
        for _ in range(3):
            frame = QFrame(); frame.setObjectName("summaryCard"); box = QVBoxLayout(frame)
            label, value = QLabel(), QLabel(); value.setObjectName("summaryValue"); box.addWidget(label); box.addWidget(value)
            self.cards.append((label, value, frame)); card_row.addWidget(frame)
        layout.addLayout(card_row)
        self.overview_table, self.overview_pager = self._build_table_area(layout, "expense", "overview")
        self.tabs.addTab(self.overview, "Overview")

    def _build_expenses(self):
        self.expenses_page = QWidget(); layout = QVBoxLayout(self.expenses_page)
        self.expense_form_heading = QLabel(); layout.addWidget(self.expense_form_heading)
        form = QFormLayout(); self.expense_amount = QLineEdit(); self.expense_amount.setPlaceholderText("0.00")
        self.expense_date = CalendarDateInput(lambda: self.calendar)
        self.expense_category = QComboBox(); self.expense_category.setEditable(True)
        self.expense_description = QLineEdit(); self.expense_description.setMaxLength(240)
        self.expense_amount_label, self.expense_date_label = QLabel(), QLabel()
        self.expense_category_label, self.expense_description_label = QLabel(), QLabel()
        form.addRow(self.expense_amount_label, self.expense_amount); form.addRow(self.expense_date_label, self.expense_date)
        form.addRow(self.expense_category_label, self.expense_category); form.addRow(self.expense_description_label, self.expense_description)
        layout.addLayout(form); actions = QHBoxLayout()
        self.expense_save_button = QPushButton(); self.expense_save_button.clicked.connect(self.save_expense)
        self.expense_delete_button = QPushButton(); self.expense_delete_button.setObjectName("dangerButton"); self.expense_delete_button.clicked.connect(self.delete_expense)
        self.expense_clear_button = QPushButton(); self.expense_clear_button.clicked.connect(self.clear_expense_form)
        actions.addWidget(self.expense_save_button); actions.addWidget(self.expense_delete_button); actions.addWidget(self.expense_clear_button); actions.addStretch()
        layout.addLayout(actions); self.expense_table, self.expense_pager = self._build_table_area(layout, "expense", "expenses")
        self.tabs.addTab(self.expenses_page, "Expenses")

    def _build_income(self):
        self.income_widget = QWidget(); layout = QVBoxLayout(self.income_widget)
        self.income_form_heading = QLabel(); layout.addWidget(self.income_form_heading)
        form = QFormLayout(); self.income_amount = QLineEdit(); self.income_amount.setPlaceholderText("0.00")
        self.income_month_input = CalendarMonthInput(lambda: self.calendar)
        self.income_source = QLineEdit(); self.income_source.setMaxLength(100)
        self.income_amount_label, self.income_month_label, self.income_source_label = QLabel(), QLabel(), QLabel()
        form.addRow(self.income_amount_label, self.income_amount); form.addRow(self.income_month_label, self.income_month_input); form.addRow(self.income_source_label, self.income_source)
        layout.addLayout(form); self.income_save_button = QPushButton(); self.income_save_button.clicked.connect(self.save_income); layout.addWidget(self.income_save_button, alignment=Qt.AlignmentFlag.AlignLeft)
        self.income_table, self.income_pager = self._build_table_area(layout, "income")
        self.income_delete_button = QPushButton("Delete selected income"); self.income_delete_button.setObjectName("dangerButton")
        self.income_delete_button.clicked.connect(self.delete_income); layout.addWidget(self.income_delete_button, alignment=Qt.AlignmentFlag.AlignLeft)
        self.tabs.addTab(self.income_widget, "Income")

    def _build_analytics(self):
        self.analytics_page = QWidget(); layout = QVBoxLayout(self.analytics_page)
        self.analytics_heading = QLabel(); layout.addWidget(self.analytics_heading)
        self.chart_mode = QComboBox()
        for label, value in (("Spending by month", "spending"), ("Income vs spending", "comparison"), ("By category", "category")):
            self.chart_mode.addItem(label, value)
        self.chart_mode.currentIndexChanged.connect(self.refresh_months)
        chart_controls = QHBoxLayout(); chart_controls.addWidget(self.chart_mode)
        self.graph_pdf_button, self.graph_print_button = QPushButton(), QPushButton()
        self.graph_pdf_button.clicked.connect(self.export_graph); self.graph_print_button.clicked.connect(self.print_graph)
        chart_controls.addWidget(self.graph_pdf_button); chart_controls.addWidget(self.graph_print_button); chart_controls.addStretch()
        layout.addLayout(chart_controls)
        try:
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
            from matplotlib.figure import Figure
            self.figure = Figure(figsize=(8, 3), tight_layout=True); self.chart_canvas = FigureCanvasQTAgg(self.figure)
            layout.addWidget(self.chart_canvas, 2)
        except Exception:
            self.figure = None; self.chart_canvas = QLabel("Install matplotlib to show charts."); layout.addWidget(self.chart_canvas)
        self.month_table, self.month_pager = self._build_table_area(layout, "month")
        self.tabs.addTab(self.analytics_page, "Analytics")

    def _build_settings(self):
        self.settings_page = QWidget(); layout = QVBoxLayout(self.settings_page)
        form = QFormLayout(); self.language_picker = QComboBox(); self.language_picker.addItems(["English", "Dari"])
        self.calendar_picker = QComboBox(); self.calendar_picker.addItem("Gregorian", "Gregorian"); self.calendar_picker.addItem("Afghan Solar Hijri", "Afghan Solar Hijri")
        self.language_picker.setCurrentText(self.language); self.calendar_picker.setCurrentIndex(0 if self.calendar == "Gregorian" else 1)
        self.language_picker.currentTextChanged.connect(self._set_language); self.calendar_picker.currentIndexChanged.connect(lambda _index: self._set_calendar(self.calendar_picker.currentData()))
        self.language_label, self.calendar_label = QLabel(), QLabel()
        form.addRow(self.language_label, self.language_picker); form.addRow(self.calendar_label, self.calendar_picker); layout.addLayout(form)
        self.safe_note = QLabel(); self.safe_note.setWordWrap(True); layout.addWidget(self.safe_note)
        self.data_location_label = QLabel(); self.data_location_label.setWordWrap(True); layout.addWidget(self.data_location_label)
        actions = QHBoxLayout(); self.backup_button = QPushButton(); self.backup_button.clicked.connect(self.create_backup)
        self.restore_button = QPushButton(); self.restore_button.clicked.connect(self.restore_backup)
        actions.addWidget(self.backup_button); actions.addWidget(self.restore_button); layout.addLayout(actions); layout.addStretch()
        self.tabs.addTab(self.settings_page, "Settings")

    def _build_table_area(self, layout, kind, role=None):
        controls = QHBoxLayout(); search = QLineEdit(); search.setPlaceholderText("Search")
        sort = QComboBox()
        for label, value in (("Recently added", "recent"), ("Oldest first", "oldest"), ("Highest amount", "highest"), ("Lowest amount", "lowest")):
            sort.addItem(label, value)
        size = QComboBox(); size.addItems(["10", "20", "50", "100"]); size.setCurrentText(str(self.page_size))
        search.textChanged.connect(lambda _value, k=kind, r=role: self._search_changed(k, r))
        sort.currentIndexChanged.connect(lambda _index, k=kind, r=role, control=sort: self._sort_changed(k, control.currentData(), r))
        size.currentTextChanged.connect(lambda value, k=kind: self._size_changed(k, int(value)))
        sort_label, size_label = QLabel(), QLabel()
        self.control_labels.append((sort_label, size_label))
        controls.addWidget(search, 2); controls.addWidget(sort_label); controls.addWidget(sort); controls.addWidget(size_label); controls.addWidget(size)
        layout.addLayout(controls)
        table = QTableWidget(0, 5 if kind == "expense" else (4 if kind == "income" else 2))
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows); table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        if kind in {"expense", "income"}: table.setColumnHidden(0, True)
        if kind == "expense": table.itemSelectionChanged.connect(lambda: self._select_expense(table))
        if kind == "income": table.itemSelectionChanged.connect(lambda: self._select_income(table))
        layout.addWidget(table, 3)
        pager = QHBoxLayout(); previous, page_label, next_button = QPushButton("Previous"), QLabel("Page 1"), QPushButton("Next")
        previous.clicked.connect(lambda _=False, k=kind, r=role: self._page_changed(k, -1, r)); next_button.clicked.connect(lambda _=False, k=kind, r=role: self._page_changed(k, 1, r))
        pager.addWidget(previous); pager.addWidget(page_label); pager.addWidget(next_button); pager.addStretch()
        export, pdf, print_button = QPushButton("Share / export CSV"), QPushButton("Save PDF"), QPushButton(TEXT["English"]["print_page"])
        export.clicked.connect(lambda _=False, t=table, k=kind, r=role: self.export_table(t, k, "csv", r))
        pdf.clicked.connect(lambda _=False, t=table, k=kind, r=role: self.export_table(t, k, "pdf", r))
        print_button.clicked.connect(lambda _=False, t=table, k=kind: self.print_table(t, k))
        pager.addWidget(export); pager.addWidget(pdf); pager.addWidget(print_button); layout.addLayout(pager)
        if kind == "expense" and role == "overview":
            self.overview_search, self.overview_sort_picker, self.overview_size_picker = search, sort, size
            return table, (previous, page_label, next_button)
        if kind == "expense": self.expense_search, self.expense_sort_picker, self.expense_size_picker = search, sort, size
        if kind == "income": self.income_search, self.income_sort_picker, self.income_size_picker = search, sort, size
        if kind == "month": self.month_search, self.month_sort_picker, self.month_size_picker = search, sort, size
        return table, (previous, page_label, next_button)

    def apply_language(self):
        text = TEXT[self.language]
        self.setWindowTitle(text["title"])
        for index, key in enumerate(("overview", "expenses", "income", "analytics", "settings")):
            self.tabs.setTabText(index, text[key])
        self.overview_heading.setText(text["overview"]); self.expense_form_heading.setText(text["new_expense"])
        self.income_form_heading.setText(text["new_income"]); self.analytics_heading.setText(text["report"])
        self.expense_save_button.setText(text["save"] if self.selected_expense_id else text["add"])
        self.expense_delete_button.setText(text["delete"]); self.income_save_button.setText(text["add"])
        self.expense_clear_button.setText(text["clear"]); self.income_delete_button.setText(text["delete_income"])
        self.overview_month_label.setText(text["month_label"])
        self.expense_amount_label.setText(text["amount_label"]); self.expense_date_label.setText(text["date_label"])
        self.expense_category_label.setText(text["category_label"]); self.expense_description_label.setText(text["description_label"])
        self.income_amount_label.setText(text["amount_label"]); self.income_month_label.setText(text["month_label"])
        self.income_source_label.setText(text["source"]); self.language_label.setText(text["language_label"])
        self.calendar_label.setText(text["calendar_label"])
        self.calendar_picker.setItemText(0, text["gregorian_calendar"]); self.calendar_picker.setItemText(1, text["solar_calendar"])
        for sort_label, size_label in self.control_labels:
            sort_label.setText(text["sort_by"]); size_label.setText(text["page_size"])
        self.graph_pdf_button.setText(text["graph_pdf"]); self.graph_print_button.setText(text["print_graph"])
        for index, key in enumerate(("spending_chart", "comparison_chart", "category_chart")):
            self.chart_mode.setItemText(index, text[key])
        self.backup_button.setText(text["backup"]); self.restore_button.setText(text["restore"]); self.safe_note.setText(text["safe_note"])
        for pager in (self.overview_pager, self.expense_pager, self.income_pager, self.month_pager):
            pager[0].setText(text["previous"]); pager[2].setText(text["next"])
        for table_controls in (self.overview_sort_picker, self.expense_sort_picker, self.income_sort_picker, self.month_sort_picker):
            table_controls.setItemText(0, text["recent"]); table_controls.setItemText(1, text["oldest"])
            table_controls.setItemText(2, text["highest"]); table_controls.setItemText(3, text["lowest"])
        for table in (self.overview_table, self.expense_table, self.income_table, self.month_table):
            area = table.parentWidget()
            if area:
                for button in area.findChildren(QPushButton):
                    if button.text() in {"Share / export CSV", "اشتراک / خروجی CSV"}: button.setText(text["export_csv"])
                    elif button.text() in {"Save PDF", "ذخیره PDF"}: button.setText(text["export_pdf"])
                    elif button.text() in {"Print this page", "چاپ این صفحه"}: button.setText(text["print_page"])
        for control in (self.overview_search, self.expense_search, self.income_search, self.month_search):
            control.setPlaceholderText(text["search"])
        self.data_location_label.setText(f"{text['data_file']}: {self.store.path}")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft if self.language == "Dari" else Qt.LayoutDirection.LeftToRight)
        self.setFont(QFont("Vazirmatn" if self.language == "Dari" else "Segoe UI", 10))
        self.expense_date.set_calendar_visibility()
        self.refresh_all()

    def _set_language(self, value):
        self.language = value; self.store.set_preference("language", value); self.apply_language()

    def _set_calendar(self, value):
        overview_month, income_month, expense_date = self.month_picker.value(), self.income_month_input.value(), self.expense_date.value()
        self.calendar = value; self.store.set_preference("calendar", value)
        self.expense_date.set_calendar_visibility(); self.month_picker.set_calendar_visibility(); self.income_month_input.set_calendar_visibility()
        self.expense_date.set_value(expense_date); self.month_picker.set_value(overview_month); self.income_month_input.set_value(income_month)
        self.refresh_all()

    def _search_changed(self, kind, role=None):
        if kind == "expense":
            if role == "overview": self.overview_page = 1
            else: self.expense_page = 1
        elif kind == "income": self.income_page = 1
        elif kind == "month": self.month_page = 1
        self.refresh_all()

    def _sort_changed(self, kind, value, role=None):
        if kind == "expense" and role == "overview": self.overview_sort = value; self.overview_page = 1
        elif kind == "expense": self.expense_sort = value; self.expense_page = 1
        elif kind == "income": self.income_sort = value; self.income_page = 1
        else: self.month_sort = value; self.month_page = 1
        self.refresh_all()

    def _size_changed(self, _kind, value):
        self.page_size = value; self.overview_page = self.expense_page = self.income_page = self.month_page = 1
        for name in ("overview_size_picker", "expense_size_picker", "income_size_picker", "month_size_picker"):
            picker = getattr(self, name, None)
            if picker and picker.currentText() != str(value): picker.setCurrentText(str(value))
        self.refresh_all()

    def _page_changed(self, kind, delta, role=None):
        if kind == "income": self.income_page = max(1, self.income_page + delta)
        elif kind == "month": self.month_page = max(1, self.month_page + delta)
        elif role == "overview": self.overview_page = max(1, self.overview_page + delta)
        else: self.expense_page = max(1, self.expense_page + delta)
        self.refresh_all()

    def _fill_table(self, table, headers, rows):
        table.clear(); table.setColumnCount(len(headers)); table.setHorizontalHeaderLabels(headers); table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column, value in enumerate(row):
                item = QTableWidgetItem(str(value)); item.setData(Qt.ItemDataRole.UserRole, value)
                table.setItem(row_index, column, item)
        table.setAlternatingRowColors(True)

    def refresh_all(self):
        try:
            self.refresh_overview(); self.refresh_expenses(); self.refresh_income(); self.refresh_months()
            self.expense_category.clear(); self.expense_category.addItems(self.store.categories())
        except sqlite3.Error as error:
            message, _diagnostic = database_error_help(error)
            QMessageBox.critical(self, self.tr("title"), message)

    def refresh_overview(self, *_):
        start, end = self.month_picker.bounds()
        summary = self.store.summary(start, period_start=start, period_end=end)
        for (label, value_label, _frame), key, field in zip(self.cards, ("income_total", "spending", "remaining"), ("income", "spending", "remaining")):
            label.setText(self.tr(key)); value_label.setText(amount_text(summary[field]))
        rows, total = self.store.page_expenses(self.overview_page, self.page_size, self.overview_sort, search=self.overview_search.text(), start=start, end=end)
        self._fill_table(self.overview_table, ("ID", self.tr("date"), self.tr("amount"), self.tr("category"), self.tr("description")),
                         [(r["id"], self.display_date(r["date"]), amount_text(r["amount"]), r["category"], r["description"]) for r in rows])
        self._update_pager(self.overview_pager, self.overview_page, total)

    def display_date(self, value):
        return format_jalali_date(date.fromisoformat(value)) if self.calendar == "Afghan Solar Hijri" else value

    def display_month(self, value):
        if self.calendar == "Afghan Solar Hijri" and len(value) == 7:
            from jalali_calendar import AFGHAN_MONTHS
            year, month = map(int, value.split("-"))
            return f"{AFGHAN_MONTHS[month - 1]} {year}"
        if self.calendar == "Afghan Solar Hijri":
            from jalali_calendar import format_jalali_month
            return format_jalali_month(date.fromisoformat(value))
        return value[:7]

    def refresh_expenses(self):
        if not hasattr(self, "expense_table"): return
        query = self.expense_search.text() if hasattr(self, "expense_search") else ""
        rows, total = self.store.page_expenses(self.expense_page, self.page_size, self.expense_sort, search=query)
        self._fill_table(self.expense_table, ("ID", self.tr("date"), self.tr("amount"), self.tr("category"), self.tr("description")),
                         [(r["id"], self.display_date(r["date"]), amount_text(r["amount"]), r["category"], r["description"]) for r in rows])
        self._update_pager(self.expense_pager, self.expense_page, total)

    def refresh_income(self):
        if not hasattr(self, "income_table"): return
        rows, total = self.store.page_income(self.income_page, self.page_size, self.income_sort, search=self.income_search.text())
        self._fill_table(self.income_table, ("ID", self.tr("month"), self.tr("amount"), self.tr("source")),
                         [(r["id"], self.display_month(r["month"]), amount_text(r["amount"]), r["source"]) for r in rows])
        self._update_pager(self.income_pager, self.income_page, total)

    def refresh_months(self):
        if not hasattr(self, "month_table"): return
        rows, total = self.store.page_months(self.month_page, self.page_size, self.month_sort, self.calendar, self.month_search.text())
        self._fill_table(self.month_table, (self.tr("month"), self.tr("spending")), [(self.display_month(r["month"]), amount_text(r["spending"])) for r in rows])
        self._update_pager(self.month_pager, self.month_page, total)
        if self.figure:
            self.figure.clear(); axis = self.figure.add_subplot(111)
            all_months = self.store.monthly_comparison(self.calendar)
            mode = self.chart_mode.currentData()
            if mode == "category":
                categories = self.store.spending_by_category()
                if categories:
                    palette = ["#176b72", "#2a9d8f", "#e9c46a", "#f4a261", "#e76f51", "#536dfe", "#9c4dcc"]
                    axis.pie([float(value) for _name, value in categories], labels=[shape_rtl(name) for name, _value in categories], colors=[palette[index % len(palette)] for index in range(len(categories))], autopct="%1.0f%%", startangle=90)
                else:
                    axis.text(.5, .5, shape_rtl(self.tr("empty")), ha="center", va="center", transform=axis.transAxes); axis.set_axis_off()
            elif all_months:
                positions = list(range(len(all_months))); months = [shape_rtl(self.display_month(entry["month"])) for entry in all_months]
                palette = ["#176b72", "#2a9d8f", "#e9c46a", "#f4a261", "#e76f51", "#536dfe", "#9c4dcc"]
                if mode == "comparison":
                    axis.bar([position - .2 for position in positions], [float(entry["income"]) for entry in all_months], width=.4, label=shape_rtl(self.tr("income_series")), color="#2a9d8f")
                    axis.bar([position + .2 for position in positions], [float(entry["spending"]) for entry in all_months], width=.4, label=shape_rtl(self.tr("spending_series")), color="#e76f51")
                    axis.legend()
                else:
                    axis.bar(positions, [float(entry["spending"]) for entry in all_months], color=[palette[i % len(palette)] for i in positions])
                axis.set_xticks(positions, months); axis.set_ylabel("AFN"); axis.tick_params(axis="x", rotation=45)
            else:
                axis.text(.5, .5, shape_rtl(self.tr("empty")), ha="center", va="center", transform=axis.transAxes); axis.set_axis_off()
            self.chart_canvas.draw()

    def export_graph(self):
        if not self.figure: return
        target, _ = QFileDialog.getSaveFileName(self, self.tr("graph_pdf"), "expense-chart.pdf", "PDF (*.pdf)")
        if not target: return
        try:
            export_figure_pdf(self.figure, target)
            QDesktopServices.openUrl(QUrl.fromLocalFile(target))
        except (OSError, RuntimeError) as error:
            QMessageBox.warning(self, self.tr("title"), f"Could not export graph: {error}")

    def print_graph(self):
        if not self.figure: return
        printer = QPrinter(QPrinter.PrinterMode.HighResolution); dialog = QPrintDialog(printer, self)
        if dialog.exec() != QPrintDialog.DialogCode.Accepted: return
        output = BytesIO(); self.figure.savefig(output, format="png", dpi=180, bbox_inches="tight")
        image = QImage.fromData(output.getvalue(), "PNG")
        document = QTextDocument(); document.addResource(QTextDocument.ResourceType.ImageResource, QUrl("expense-chart.png"), image)
        document.setHtml("<html><meta charset='utf-8'><body><img src='expense-chart.png' width='100%'></body></html>")
        document.print(printer)

    def _update_pager(self, pager, page, total):
        pages = max(1, (total + self.page_size - 1) // self.page_size)
        previous, label, next_button = pager
        label.setText(f"{self.tr('page')} {page} / {pages}  ·  {total}")
        previous.setEnabled(page > 1); next_button.setEnabled(page < pages)

    def _select_expense(self, table):
        row = table.currentRow()
        if row < 0: return
        try: expense_id = int(table.item(row, 0).text())
        except (AttributeError, ValueError): return
        selected = self.store.get_expense(expense_id)
        if not selected: return
        self.selected_expense_id = expense_id; self.expense_amount.setText(str(selected["amount"]))
        self.expense_date.set_value(date.fromisoformat(selected["date"])); self.expense_category.setCurrentText(selected["category"])
        self.expense_description.setText(selected["description"]); self.expense_save_button.setText(self.tr("save"))

    def _select_income(self, table):
        row = table.currentRow()
        if row >= 0:
            try: self.selected_income_id = int(table.item(row, 0).text())
            except (AttributeError, ValueError): self.selected_income_id = None

    def clear_expense_form(self):
        self.selected_expense_id = None; self.expense_amount.clear(); self.expense_description.clear()
        self.expense_date.set_value(date.today()); self.expense_save_button.setText(self.tr("add"))

    def save_expense(self):
        try:
            values = (self.expense_amount.text(), self.expense_date.value(), self.expense_description.text(), self.expense_category.currentText())
            if self.selected_expense_id: self.store.update_expense(self.selected_expense_id, *values)
            else: self.store.add_expense(*values)
            self.clear_expense_form(); self.refresh_all(); QMessageBox.information(self, self.tr("title"), self.tr("saved"))
        except sqlite3.Error as error:
            message, _diagnostic = database_error_help(error); QMessageBox.warning(self, self.tr("title"), message)
        except (ValueError, LookupError, OSError) as error:
            QMessageBox.warning(self, self.tr("title"), str(error))

    def delete_expense(self):
        if not self.selected_expense_id:
            QMessageBox.information(self, self.tr("title"), self.tr("choose_record")); return
        if QMessageBox.question(self, self.tr("title"), self.tr("confirm_delete")) == QMessageBox.StandardButton.Yes:
            try: self.store.delete_expense(self.selected_expense_id); self.clear_expense_form(); self.refresh_all()
            except sqlite3.Error as error:
                message, _diagnostic = database_error_help(error); QMessageBox.warning(self, self.tr("title"), message)
            except (ValueError, LookupError, OSError) as error: QMessageBox.warning(self, self.tr("title"), str(error))

    def delete_income(self):
        if not self.selected_income_id:
            QMessageBox.information(self, self.tr("title"), self.tr("choose_record")); return
        if QMessageBox.question(self, self.tr("title"), self.tr("confirm_delete")) == QMessageBox.StandardButton.Yes:
            try:
                self.store.delete_income(self.selected_income_id); self.selected_income_id = None; self.refresh_all()
            except sqlite3.Error as error:
                message, _diagnostic = database_error_help(error); QMessageBox.warning(self, self.tr("title"), message)
            except (ValueError, LookupError, OSError) as error:
                QMessageBox.warning(self, self.tr("title"), str(error))

    def save_income(self):
        try:
            self.store.add_income(self.income_amount.text(), self.income_month_input.value(), self.income_source.text())
            self.income_amount.clear(); self.income_source.clear(); self.refresh_all()
            QMessageBox.information(self, self.tr("title"), self.tr("saved"))
        except sqlite3.Error as error:
            message, _diagnostic = database_error_help(error); QMessageBox.warning(self, self.tr("title"), message)
        except (ValueError, OSError) as error: QMessageBox.warning(self, self.tr("title"), str(error))

    def create_backup(self):
        target, _ = QFileDialog.getSaveFileName(self, self.tr("backup"), str(default_database_path().parent / "expense-tracker-backup.json"), "JSON backup (*.json)")
        if not target: return
        try:
            saved = self.store.backup(target); QMessageBox.information(self, self.tr("title"), f"Backup saved to:\n{saved}")
        except sqlite3.Error as error:
            message, _diagnostic = database_error_help(error); QMessageBox.critical(self, self.tr("title"), message)
        except OSError as error: QMessageBox.critical(self, self.tr("title"), f"Could not create backup: {error}")

    def restore_backup(self):
        source, _ = QFileDialog.getOpenFileName(self, self.tr("restore"), "", "JSON backup (*.json)")
        if not source: return
        if QMessageBox.question(self, self.tr("title"), "Restore only works in an empty profile. Continue?") != QMessageBox.StandardButton.Yes: return
        try:
            counts = self.store.restore(source); self.refresh_all()
            QMessageBox.information(self, self.tr("title"), f"Restored {counts[0]} expenses and {counts[1]} income records.")
        except sqlite3.Error as error:
            message, _diagnostic = database_error_help(error); QMessageBox.warning(self, self.tr("title"), message)
        except (ValueError, OSError) as error: QMessageBox.warning(self, self.tr("title"), str(error))

    def _table_rows(self, table):
        columns = [column for column in range(table.columnCount()) if not table.isColumnHidden(column)]
        headers = [table.horizontalHeaderItem(i).text() for i in columns]
        rows = [[table.item(r, c).text() if table.item(r, c) else "" for c in columns] for r in range(table.rowCount())]
        return headers, rows

    def _complete_report_rows(self, kind, role=None):
        page_size = 100
        if kind == "expense":
            if role == "overview":
                start, end = self.month_picker.bounds()
                query, sort = self.overview_search.text(), self.overview_sort
            else:
                start = end = None; query, sort = self.expense_search.text(), self.expense_sort
            fetch = lambda page: self.store.page_expenses(page, page_size, sort, search=query, start=start, end=end)
            rows = self._collect_pages(fetch)
            return [self.tr("date"), self.tr("amount"), self.tr("category"), self.tr("description")], [
                [self.display_date(row["date"]), amount_text(row["amount"]), row["category"], row["description"]] for row in rows]
        if kind == "income":
            fetch = lambda page: self.store.page_income(page, page_size, self.income_sort, self.income_search.text())
            rows = self._collect_pages(fetch)
            return [self.tr("month"), self.tr("amount"), self.tr("source")], [
                [self.display_month(row["month"]), amount_text(row["amount"]), row["source"]] for row in rows]
        fetch = lambda page: self.store.page_months(page, page_size, self.month_sort, self.calendar, self.month_search.text())
        rows = self._collect_pages(fetch)
        return [self.tr("month"), self.tr("spending")], [
            [self.display_month(row["month"]), amount_text(row["spending"])] for row in rows]

    @staticmethod
    def _collect_pages(fetch):
        rows, count = fetch(1)
        pages = (count + 99) // 100
        for page in range(2, pages + 1): rows.extend(fetch(page)[0])
        return rows

    def export_table(self, table, kind, format_name, role=None):
        headers, rows = self._complete_report_rows(kind, role)
        if kind == "month" and format_name == "pdf" and self.figure:
            target, _ = QFileDialog.getSaveFileName(self, self.tr("export_pdf"), "monthly-spending.pdf", "PDF (*.pdf)")
            if target:
                try: export_figure_pdf(self.figure, target); QDesktopServices.openUrl(QUrl.fromLocalFile(target))
                except (OSError, RuntimeError) as error: QMessageBox.warning(self, self.tr("title"), str(error))
            return
        suffix, filter_text = ("csv", "CSV (*.csv)") if format_name == "csv" else ("pdf", "PDF (*.pdf)")
        target, _ = QFileDialog.getSaveFileName(self, "Export full filtered table", f"{kind}-report.{suffix}", filter_text)
        if not target: return
        try:
            if format_name == "csv":
                with open(target, "w", newline="", encoding="utf-8-sig") as file:
                    writer = csv.writer(file); writer.writerow(headers); writer.writerows([[_safe_cell(value) for value in row] for row in rows])
            else: export_table_pdf(self.tr(kind), headers, rows, target)
            QDesktopServices.openUrl(QUrl.fromLocalFile(target))
        except (OSError, RuntimeError) as error: QMessageBox.warning(self, self.tr("title"), f"Export failed: {error}")

    def print_table(self, table, kind):
        headers, rows = self._table_rows(table)
        document = QTextDocument(); document.setHtml(html_table(self.tr(kind), headers, rows))
        printer = QPrinter(QPrinter.PrinterMode.HighResolution); dialog = QPrintDialog(printer, self)
        if dialog.exec() == QPrintDialog.DialogCode.Accepted: document.print(printer)


def run_gui(database_path: str | Path | None = None) -> int:
    app = QApplication.instance() or QApplication([])
    app.setApplicationName("Expense Tracker")
    asset_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1])) / "assets"
    font_path = asset_root / "fonts" / "Vazirmatn-Regular.ttf"
    if font_path.exists(): QFontDatabase.addApplicationFont(str(font_path))
    configure_report_font()
    app.setFont(QFont("Segoe UI", 10))
    app.setStyleSheet("""
        QWidget { color: #17324d; font-size: 10pt; }
        QMainWindow, QWidget { background: #f5f8fb; }
        QTabWidget::pane { border: 1px solid #d8e2ea; border-radius: 8px; background: white; }
        QTabBar::tab { background: #e7eef4; padding: 10px 18px; margin: 3px; border-radius: 7px; }
        QTabBar::tab:selected { color: white; background: #176b72; }
        QLineEdit, QComboBox, QDateEdit, QSpinBox, QTableWidget { background: white; border: 1px solid #c8d5df; border-radius: 5px; padding: 6px; }
        QPushButton { background: #176b72; color: white; padding: 8px 14px; border: 0; border-radius: 6px; }
        QPushButton:hover { background: #12565c; }
        QPushButton#dangerButton { background: #b53b42; }
        QFrame#summaryCard { background: white; border: 1px solid #dce5eb; border-radius: 10px; }
        QLabel#summaryValue { font-size: 19pt; font-weight: 700; }
    """)
    try:
        window = MainWindow(database_path)
    except (sqlite3.Error, OSError) as error:
        write_debug_log(error)
        message, _diagnostic = database_error_help(error)
        QMessageBox.critical(None, "Expense Tracker", message)
        return 2
    icon_path = asset_root / "expense-tracker.ico"
    if icon_path.exists(): window.setWindowIcon(QIcon(str(icon_path)))
    window.show()
    return app.exec()

