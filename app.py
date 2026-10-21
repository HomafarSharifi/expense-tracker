"""Launch the desktop application (used by the Windows bundle)."""

import argparse
from pathlib import Path
import sys


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Start Expense Tracker desktop app")
    parser.add_argument("--db", type=Path, help="Use a specific SQLite database")
    args = parser.parse_args(argv)
    try:
        from expense_tracker.desktop import run_gui
    except ImportError as error:
        try:
            from expense_tracker.diagnostics import write_debug_log
            write_debug_log(error)
        except ImportError:
            pass
        print("The desktop interface needs its packaged Qt for Python dependency. For CLI use, run: python main.py --help", file=sys.stderr)
        print(f"Details: {error}", file=sys.stderr)
        return 2
    try:
        return run_gui(args.db)
    except Exception as error:
        try:
            from expense_tracker.diagnostics import write_debug_log
            write_debug_log(error)
        except ImportError:
            pass
        raise


if __name__ == "__main__":
    raise SystemExit(main())
