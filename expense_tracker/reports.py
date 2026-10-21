"""User-triggered CSV and PDF exports. No report is uploaded or shared automatically."""

from __future__ import annotations

import csv
from html import escape
from pathlib import Path
import sys


def _safe_cell(value: object) -> object:
    # Spreadsheet formulas in user-entered descriptions must remain inert.
    if isinstance(value, str) and value.startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + value
    return value


def shape_rtl(value: object) -> str:
    """Shape Dari/Arabic labels for Matplotlib, which does not do this itself."""
    text = str(value)
    if not any("\u0600" <= character <= "\u06ff" for character in text):
        return text
    from arabic_reshaper import reshape
    from bidi.algorithm import get_display
    return get_display(reshape(text))


def configure_report_font() -> None:
    """Use the bundled Vazirmatn font in charts and generated PDFs when available."""
    import matplotlib
    import matplotlib.font_manager as font_manager
    asset_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1])) / "assets"
    font_path = asset_root / "fonts" / "Vazirmatn-Regular.ttf"
    if font_path.exists():
        font_manager.fontManager.addfont(str(font_path))
        family = font_manager.FontProperties(fname=str(font_path)).get_name()
        matplotlib.rcParams["font.family"] = family


def export_csv(store, path: str | Path) -> int:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    rows = store.all_expenses()
    with target.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(("ID", "Date", "Amount (AFN)", "Category", "Description"))
        for row in rows:
            writer.writerow((_safe_cell(row["id"]), _safe_cell(row["date"]),
                             f"{row['amount']:.2f}", _safe_cell(row["category"]),
                             _safe_cell(row["description"])))
    return len(rows)


def export_table_pdf(title: str, headers: list[str], rows: list[list[object]], path: str | Path) -> Path:
    """Render a printable, user-selected table without network access."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages

    configure_report_font()

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    safe_rows = [[shape_rtl(value) for value in row] for row in rows] or [["No records"] + [""] * (len(headers) - 1)]
    page_size = 28
    with PdfPages(target) as pdf:
        for offset in range(0, len(safe_rows), page_size):
            page_rows = safe_rows[offset:offset + page_size]
            fig, axis = plt.subplots(figsize=(11.7, 8.3))
            axis.axis("off")
            axis.set_title(shape_rtl(title), fontsize=16, loc="left", pad=18)
            table = axis.table(cellText=page_rows, colLabels=[shape_rtl(value) for value in headers], loc="upper left", cellLoc="left")
            table.auto_set_font_size(False); table.set_fontsize(8); table.scale(1, 1.35)
            for (row, _column), cell in table.get_celld().items():
                if row == 0:
                    cell.set_facecolor("#173f5f"); cell.get_text().set_color("white")
                elif row % 2:
                    cell.set_facecolor("#f3f7fa")
            pdf.savefig(fig, bbox_inches="tight")
            plt.close(fig)
    return target


def export_figure_pdf(figure, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(target, format="pdf", bbox_inches="tight")
    return target


def html_table(title: str, headers: list[str], rows: list[list[object]]) -> str:
    """Minimal escaped HTML for OS print and browser-compatible sharing."""
    header_html = "".join(f"<th>{escape(str(value))}</th>" for value in headers)
    body_html = "".join("<tr>" + "".join(f"<td>{escape(str(value))}</td>" for value in row) + "</tr>" for row in rows)
    return f"<html><meta charset='utf-8'><h1>{escape(title)}</h1><table border='1' cellspacing='0' cellpadding='6'><thead><tr>{header_html}</tr></thead><tbody>{body_html}</tbody></table></html>"

