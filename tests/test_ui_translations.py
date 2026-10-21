import ast
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

PROJECT = Path(__file__).resolve().parents[1]
tempfile.tempdir = str(PROJECT / ".test-tmp")
Path(tempfile.tempdir).mkdir(exist_ok=True)


class UiTranslationCoverageTests(unittest.TestCase):
    def test_desktop_translation_keys_match_between_english_and_dari(self):
        tree = ast.parse((PROJECT / "expense_tracker" / "desktop.py").read_text(encoding="utf-8-sig"))
        value = next(node.value for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "TEXT" for target in node.targets))
        translations = ast.literal_eval(value)
        self.assertEqual(set(translations["English"]), set(translations["Dari"]))
        self.assertGreaterEqual(len(translations["English"]), 35)

    @unittest.skipUnless(importlib.util.find_spec("PySide6"), "Desktop dependency is not installed")
    def test_desktop_window_starts_and_switches_to_dari_and_solar_calendar(self):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtWidgets import QApplication
        from expense_tracker.desktop import MainWindow

        app = QApplication.instance() or QApplication([])
        window = MainWindow(PROJECT / ".test-tmp" / "ui-smoke.sqlite3")
        self.assertEqual(window.tabs.count(), 5)
        window.language_picker.setCurrentText("Dari")
        self.assertEqual(window.windowTitle(), "مدیریت مصارف")
        window.calendar_picker.setCurrentIndex(1)
        self.assertEqual(window.display_date("2024-03-20"), "01 حمل 1403")
        start, end = window.month_picker.bounds()
        from jalali_calendar import jalali_month_bounds
        self.assertEqual((start, end), jalali_month_bounds(start))
        income_start, income_end = window.income_month_input.bounds()
        self.assertEqual((income_start, income_end), jalali_month_bounds(income_start))
        window.close()
        app.processEvents()


if __name__ == "__main__": unittest.main()
