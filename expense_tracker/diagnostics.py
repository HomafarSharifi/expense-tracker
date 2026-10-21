"""Opt-in, local-only startup diagnostics for frozen Windows builds."""

import os
from pathlib import Path
import tempfile
import traceback


def write_debug_log(error: BaseException) -> None:
    """Write details only when a developer explicitly sets EXPENSE_DEBUG=1."""
    if os.environ.get("EXPENSE_DEBUG") != "1":
        return
    try:
        log = Path(tempfile.gettempdir()) / "ExpenseTracker-startup.log"
        log.write_text(f"{type(error).__name__}: {error}\n\n{traceback.format_exc()}", encoding="utf-8")
    except OSError:
        pass
