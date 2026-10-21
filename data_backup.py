"""Compatibility entry point for backup and restore operations."""

from expense_tracker.cli import run


if __name__ == "__main__":
    import sys
    command = sys.argv[1:]
    if command and command[0] in {"backup", "restore"}:
        raise SystemExit(run(command))
    print("Usage: python data_backup.py backup [path] | restore <path>")
    raise SystemExit(2)
