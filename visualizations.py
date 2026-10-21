"""Local chart generation helpers for scripts; no browser or database server."""
from pathlib import Path

from expense_tracker.storage import ExpenseStore, default_data_dir


def plot_monthly_spending(path=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    rows = ExpenseStore().all_months()
    if not rows: return None
    target = Path(path) if path else default_data_dir() / "monthly-spending.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, 5))
    colors = ["#176b72", "#2a9d8f", "#e9c46a", "#f4a261", "#e76f51"]
    ax.bar([r["month"] for r in rows], [float(r["spending"]) for r in rows], color=[colors[i % len(colors)] for i in range(len(rows))])
    ax.set_title("Monthly Spending"); ax.set_ylabel("AFN"); ax.tick_params(axis="x", rotation=45)
    fig.tight_layout(); fig.savefig(target); plt.close(fig)
    return target
