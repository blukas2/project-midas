from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from backend.portfolio.portfolio_analyzer import AnalysisResult


METRIC_CONFIGS = [
    # (name, attr, text_attr, suffix, change_fmt, higher_is_better)
    # Annualized Return is handled separately via _resolve_annualized_return_config()
    ("Beta (to benchmark)", "beta", "beta_text", "", "+.3f", None),
    ("Alpha (Jensen's Alpha)", "alpha", "alpha_text", "%", "+.3f", True),
    ("Information Ratio", "information_ratio", "information_ratio_text", "", "+.3f", True),
    ("Sharpe Ratio", "sharpe_ratio", "sharpe_text", "", "+.3f", True),
    ("Value at Risk (95%, Monthly)", "var_95", "var_text", "%", "+.2f", True),
    ("Conditional VaR (95%, Monthly)", "cvar_95", "cvar_text", "%", "+.2f", True),
    ("Maximum Drawdown", "max_drawdown", "max_drawdown_text", "%", "+.2f", True),
    ("Max Drawdown Duration", "max_drawdown_duration_days", "max_drawdown_duration_text", " days", "+d", False),
    ("Diversification Ratio", "diversification_ratio", "diversification_text", "", "+.3f", True),
    ("Effective Independent Bets", "effective_bets", "effective_bets_text", "", "+.2f", True),
]

POSITIVE_COLOR = "#228B22"
NEGATIVE_COLOR = "#CC0000"


class AnalyzeImpactWindow:
    """Popup window comparing current portfolio metrics with projected values after a position change."""

    def __init__(self, master, current: AnalysisResult, projected: AnalysisResult, ticker: str, quantity_change: int):
        self.current = current
        self.projected = projected
        self.window = tk.Toplevel(master)
        self.window.title("Impact Analysis")
        self.window.geometry("1100x700")
        self._build_ui(ticker, quantity_change)

    def _build_ui(self, ticker: str, quantity_change: int):
        canvas, scrollable = self._create_scrollable_frame()
        header_text = self._build_header_text(ticker, quantity_change)
        self._add_header(scrollable, header_text)

        subtitle = tk.Label(scrollable, text="Current values → projected values after the change",
                            font=("Arial", 10, "italic"), fg="#555555")
        subtitle.pack(anchor="w", padx=15, pady=(0, 10))

        metrics_frame = tk.Frame(scrollable)
        metrics_frame.pack(fill="both", expand=True, padx=5)
        self._add_metric_rows(metrics_frame)

        scrollable.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _create_scrollable_frame(self) -> tuple[tk.Canvas, tk.Frame]:
        canvas = tk.Canvas(self.window)
        scrollbar = ttk.Scrollbar(self.window, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas)
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        return canvas, scrollable

    def _add_header(self, parent: tk.Frame, text: str):
        label = tk.Label(parent, text=text, font=("Arial", 16, "bold"))
        label.pack(anchor="w", padx=15, pady=(15, 5))
        separator = ttk.Separator(parent, orient="horizontal")
        separator.pack(fill="x", padx=15, pady=(0, 10))

    def _build_header_text(self, ticker: str, quantity_change: int) -> str:
        action = "adding" if quantity_change > 0 else "removing"
        return f"Impact of {action} {abs(quantity_change)} share(s) of {ticker}"

    def _add_metric_rows(self, parent: tk.Frame):
        row_index = self._add_annualized_return_row(parent, row_index=0)
        for i, (name, attr, text_attr, suffix, change_fmt, hib) in enumerate(METRIC_CONFIGS):
            current_val = getattr(self.current, attr)
            new_val = getattr(self.projected, attr)
            description = getattr(self.current, text_attr)
            self._add_metric_row(parent, row_index + i, name, current_val, new_val, description, suffix, change_fmt, hib)

    def _add_annualized_return_row(self, parent: tk.Frame, row_index: int) -> int:
        """Add annualized return row with fallback: 10y → 5y → N/A. Returns next row_index."""
        period, available = self._resolve_annualized_return_period()
        if not available:
            return self._add_annualized_return_na_row(parent, row_index)
        name = f"Annualized Return ({period})"
        attr = f"annualized_return_{period}"
        text_attr = f"annualized_return_{period}_text"
        current_val = getattr(self.current, attr)
        new_val = getattr(self.projected, attr)
        description = getattr(self.current, text_attr)
        self._add_metric_row(parent, row_index, name, current_val, new_val, description, "%", "+.2f", True)
        return row_index + 1

    def _resolve_annualized_return_period(self) -> tuple[str, bool]:
        """Determine the best annualized return period available in the projected portfolio."""
        if self.projected.annualized_return_10y != 0.0:
            return "10y", True
        if self.projected.annualized_return_5y != 0.0:
            return "5y", True
        return "10y", False

    def _add_annualized_return_na_row(self, parent: tk.Frame, row_index: int) -> int:
        """Show current 10y return on the left and N/A on the right when data is insufficient."""
        row = row_index * 2
        current_val = self.current.annualized_return_10y
        current_str = f"{current_val}%"
        tk.Label(parent, text="Annualized Return (10y):", font=("Arial", 11, "bold")).grid(
            row=row, column=0, sticky="w", padx=(15, 5), pady=(8, 0))
        tk.Label(parent, text=current_str, font=("Arial", 11)).grid(
            row=row, column=1, sticky="w", padx=(0, 10), pady=(8, 0))
        tk.Label(parent, text="→", font=("Arial", 11)).grid(
            row=row, column=2, padx=5, pady=(8, 0))
        tk.Label(parent, text="N/A", font=("Arial", 11, "bold"), fg="#888888").grid(
            row=row, column=3, sticky="w", padx=(10, 15), pady=(8, 0))
        notice = "New asset has less than 5 years of history — annualized return comparison is not available."
        tk.Label(parent, text=notice, wraplength=500, justify="left", fg="#CC6600").grid(
            row=row + 1, column=0, columnspan=4, sticky="w", padx=(25, 0), pady=(0, 5))
        return row_index + 1

    def _add_metric_row(self, parent: tk.Frame, index: int, name: str, current_val,
                        new_val, description: str, suffix: str, change_fmt: str,
                        higher_is_better: Optional[bool]):
        row = index * 2
        current_str = self._format_value(current_val, suffix)
        tk.Label(parent, text=f"{name}:", font=("Arial", 11, "bold")).grid(
            row=row, column=0, sticky="w", padx=(15, 5), pady=(8, 0))
        tk.Label(parent, text=current_str, font=("Arial", 11)).grid(
            row=row, column=1, sticky="w", padx=(0, 10), pady=(8, 0))
        tk.Label(parent, text="→", font=("Arial", 11)).grid(
            row=row, column=2, padx=5, pady=(8, 0))

        change = new_val - current_val
        color = self._get_impact_color(change, higher_is_better)
        new_str = self._format_value(new_val, suffix)
        change_str = self._format_change(change, suffix, change_fmt)
        tk.Label(parent, text=f"{new_str} ({change_str})", font=("Arial", 11, "bold"), fg=color).grid(
            row=row, column=3, sticky="w", padx=(10, 15), pady=(8, 0))

        tk.Label(parent, text=description, wraplength=500, justify="left", fg="#555555").grid(
            row=row + 1, column=0, columnspan=2, sticky="w", padx=(25, 0), pady=(0, 5))

    def _format_value(self, value, suffix: str) -> str:
        return f"{value}{suffix}"

    def _format_change(self, change, suffix: str, change_fmt: str) -> str:
        return f"{change:{change_fmt}}{suffix}"

    def _get_impact_color(self, change, higher_is_better: Optional[bool]) -> str:
        if higher_is_better is None or change == 0:
            return "black"
        is_improvement = (change > 0) == higher_is_better
        return POSITIVE_COLOR if is_improvement else NEGATIVE_COLOR
