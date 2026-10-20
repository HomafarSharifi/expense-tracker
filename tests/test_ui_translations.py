import ast
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]


class UiTranslationCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app_tree = ast.parse((PROJECT / "app.py").read_text(encoding="utf-8"))
        cls.translations = {}
        for node in cls.app_tree.body:
            if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "TRANSLATIONS"
                for target in node.targets
            ):
                cls.translations = ast.literal_eval(node.value)

    def test_literal_translated_ui_strings_have_a_dari_entry(self):
        untranslated = []
        for node in ast.walk(self.app_tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "t"
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
                and node.args[0].value not in self.translations
            ):
                untranslated.append((node.lineno, node.args[0].value))
        self.assertEqual(untranslated, [])

    def test_database_error_messages_have_dari_translations(self):
        errors_tree = ast.parse(
            (PROJECT / "database_errors.py").read_text(encoding="utf-8")
        )
        missing = sorted({
            node.value
            for node in ast.walk(errors_tree)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node.value.startswith(("The ", "A ", "Could not "))
            and node.value not in self.translations
        })
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
