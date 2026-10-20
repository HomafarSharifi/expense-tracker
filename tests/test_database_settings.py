import os
import unittest
from unittest.mock import patch

import database


class DatabaseSettingsTests(unittest.TestCase):
    def test_environment_variables_override_defaults(self):
        values = {
            "EXPENSE_DB_HOST": "db.example.test",
            "EXPENSE_DB_PORT": "3307",
            "EXPENSE_DB_USER": "tracker",
            "EXPENSE_DB_PASSWORD": "secret",
            "EXPENSE_DB_NAME": "expenses",
            "EXPENSE_DB_CONNECT_TIMEOUT": "9",
        }
        with patch.dict(os.environ, values):
            with patch.object(database.mysql.connector, "connect") as connect:
                database.get_connection()
        connect.assert_called_once_with(
            host="db.example.test",
            port=3307,
            user="tracker",
            password="secret",
            database="expenses",
            connection_timeout=9,
        )

    def test_missing_local_streamlit_secrets_fall_back_cleanly(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("EXPENSE_TEST_MISSING_SETTING", None)
            self.assertEqual(
                database._setting("EXPENSE_TEST_MISSING_SETTING", "default"),
                "default",
            )

    def test_public_settings_never_include_password(self):
        values = {
            "EXPENSE_DB_HOST": "localhost",
            "EXPENSE_DB_PORT": "3307",
            "EXPENSE_DB_USER": "tracker",
            "EXPENSE_DB_PASSWORD": "private-value",
            "EXPENSE_DB_NAME": "expenses",
        }
        with patch.dict(os.environ, values):
            settings = database.get_public_connection_settings()
        self.assertEqual(settings["port"], "3307")
        self.assertEqual(settings["database"], "expenses")
        self.assertNotIn("password", settings)
        self.assertNotIn("private-value", repr(settings))


if __name__ == "__main__":
    unittest.main()
