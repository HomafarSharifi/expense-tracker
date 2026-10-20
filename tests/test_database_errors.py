import unittest

from database_errors import database_error_help


class MySqlError(Exception):
    def __init__(self, errno, msg=""):
        super().__init__(msg)
        self.errno = errno
        self.msg = msg


class DatabaseErrorHelpTests(unittest.TestCase):
    def test_invalid_connection_settings_get_actionable_help(self):
        message, diagnostic = database_error_help(ValueError("invalid port"))
        self.assertIn("port and connection timeout", message)
        self.assertEqual(diagnostic, "ValueError")

    def test_permission_error_has_specific_recovery_steps(self):
        message, _ = database_error_help(MySqlError(1044, "access denied"))
        self.assertIn("lacks permission", message)

    def test_sensitive_login_details_are_not_shown(self):
        message, diagnostic = database_error_help(
            MySqlError(1045, "password=do-not-display")
        )
        self.assertIn("rejected the login", message)
        self.assertNotIn("do-not-display", diagnostic)


if __name__ == "__main__":
    unittest.main()
