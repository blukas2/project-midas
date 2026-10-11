from __future__ import annotations

import customtkinter as ctk

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
        self.window = ctk.CTkToplevel(master)
        self.window.title("Impact Analysis")
        self.window.geometry("1100x700")
        self._build_ui(ticker, quantity_change)

    def _build_ui(self, ticker: str, quantity_change: int):
        scrollable = self._create_scrollable_frame()
        header_text = self._build_header_text(ticker, quantity_change)
        self._add_header(scrollable, header_text)

        subtitle = ctk.CTkLabel(
            scrollable,
            text="Current values → projected values after the change",
            font=("Arial", 10, "italic"),
            text_color=("gray35", "gray75"),
        )
        subtitle.pack(anchor="w", padx=15, pady=(0, 10))

        metrics_frame = ctk.CTkFrame(scrollable)
        metrics_frame.pack(fill="both", expand=True, padx=5)
        self._add_metric_rows(metrics_frame)

    def _create_scrollable_frame(self) -> ctk.CTkScrollableFrame:
        scrollable = ctk.CTkScrollableFrame(self.window)
        scrollable.pack(fill="both", expand=True)
        return scrollable

    def _add_header(self, parent: ctk.CTkFrame, text: str):
        label = ctk.CTkLabel(parent, text=text, font=("Arial", 16, "bold"))
        label.pack(anchor="w", padx=15, pady=(15, 5))
        ctk.CTkFrame(parent, height=2, fg_color=("gray75", "gray30")).pack(fill="x", padx=15, pady=(0, 10))

    def _build_header_text(self, ticker: str, quantity_change: int) -> str:
        action = "adding" if quantity_change > 0 else "removing"
        return f"Impact of {action} {abs(quantity_change)} share(s) of {ticker}"

    def _add_metric_rows(self, parent: ctk.CTkFrame):
        row_index = self._add_annualized_return_row(parent, row_index=0)
        for i, (name, attr, text_attr, suffix, change_fmt, hib) in enumerate(METRIC_CONFIGS):
            current_val = getattr(self.current, attr)
            new_val = getattr(self.projected, attr)
            description = getattr(self.current, text_attr)
            self._add_metric_row(parent, row_index + i, name, current_val, new_val, description, suffix, change_fmt, hib)

    def _add_annualized_return_row(self, parent: ctk.CTkFrame, row_index: int) -> int:
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

    def _add_annualized_return_na_row(self, parent: ctk.CTkFrame, row_index: int) -> int:
        """Show current 10y return on the left and N/A on the right when data is insufficient."""
        row = row_index * 2
        current_val = self.current.annualized_return_10y
        current_str = f"{current_val}%"
        ctk.CTkLabel(parent, text="Annualized Return (10y):", font=("Arial", 11, "bold")).grid(
            row=row, column=0, sticky="w", padx=(15, 5), pady=(8, 0))
        ctk.CTkLabel(parent, text=current_str, font=("Arial", 11)).grid(
            row=row, column=1, sticky="w", padx=(0, 10), pady=(8, 0))
        ctk.CTkLabel(parent, text="→", font=("Arial", 11)).grid(
            row=row, column=2, padx=5, pady=(8, 0))
        ctk.CTkLabel(parent, text="N/A", font=("Arial", 11, "bold"), text_color=("gray45", "gray70")).grid(
            row=row, column=3, sticky="w", padx=(10, 15), pady=(8, 0))
        notice = "New asset has less than 5 years of history — annualized return comparison is not available."
        ctk.CTkLabel(parent, text=notice, wraplength=500, justify="left", text_color="#CC6600").grid(
            row=row + 1, column=0, columnspan=4, sticky="w", padx=(25, 0), pady=(0, 5))
        return row_index + 1

    def _add_metric_row(self, parent: ctk.CTkFrame, index: int, name: str, current_val,
                        new_val, description: str, suffix: str, change_fmt: str,
                        higher_is_better: Optional[bool]):
        row = index * 2
        current_str = self._format_value(current_val, suffix)
        ctk.CTkLabel(parent, text=f"{name}:", font=("Arial", 11, "bold")).grid(
            row=row, column=0, sticky="w", padx=(15, 5), pady=(8, 0))
        ctk.CTkLabel(parent, text=current_str, font=("Arial", 11)).grid(
            row=row, column=1, sticky="w", padx=(0, 10), pady=(8, 0))
        ctk.CTkLabel(parent, text="→", font=("Arial", 11)).grid(
            row=row, column=2, padx=5, pady=(8, 0))

        change = new_val - current_val
        color = self._get_impact_color(change, higher_is_better)
        new_str = self._format_value(new_val, suffix)
        change_str = self._format_change(change, suffix, change_fmt)
        ctk.CTkLabel(parent, text=f"{new_str} ({change_str})", font=("Arial", 11, "bold"), text_color=color).grid(
            row=row, column=3, sticky="w", padx=(10, 15), pady=(8, 0))

        ctk.CTkLabel(parent, text=description, wraplength=500, justify="left", text_color=("gray35", "gray75")).grid(
            row=row + 1, column=0, columnspan=2, sticky="w", padx=(25, 0), pady=(0, 5))

    def _format_value(self, value, suffix: str) -> str:
        return f"{value}{suffix}"

    def _format_change(self, change, suffix: str, change_fmt: str) -> str:
        return f"{change:{change_fmt}}{suffix}"

    def _get_impact_color(self, change, higher_is_better: Optional[bool]) -> str | tuple[str, str]:
        if higher_is_better is None or change == 0:
            return ("gray15", "gray90")
        is_improvement = (change > 0) == higher_is_better
        return POSITIVE_COLOR if is_improvement else NEGATIVE_COLOR
