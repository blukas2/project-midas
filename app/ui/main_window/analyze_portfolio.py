from __future__ import annotations

import customtkinter as ctk
from tkinter import ttk

from typing import TYPE_CHECKING
from ui.dialogs import ThemedMessageBox as msgbox
if TYPE_CHECKING:
    from backend.backend import BackEnd
    from backend.portfolio.portfolio_analyzer import AnalysisResult


class AnalyzePortfolioWindow:
    """Popup window that displays advanced portfolio risk/return metrics."""

    def __init__(self, master, backend: BackEnd):
        self.backend = backend
        self.window = ctk.CTkToplevel(master)
        self.window.title("Portfolio Analysis")
        self.window.geometry("1100x700")
        self._run_analysis()

    def _run_analysis(self):
        if not self.backend.portfolio.content:
            msgbox.showwarning("No Data", "Portfolio is empty. Add assets first.", parent=self.window)
            self.window.destroy()
            return
        try:
            result = self.backend.analyze_portfolio()
        except Exception as e:
            msgbox.showerror("Analysis Error", str(e), parent=self.window)
            self.window.destroy()
            return
        self._build_ui(result)

    def _build_ui(self, result: AnalysisResult):
        self._metrics: list[tuple[str, str]] = []
        scrollable = self._create_scrollable_frame()
        self._add_header(scrollable, "Portfolio Analysis")

        columns_frame = ctk.CTkFrame(scrollable)
        columns_frame.pack(fill="both", expand=True, padx=5)

        left_frame = ctk.CTkFrame(columns_frame)
        left_frame.pack(side="left", fill="both", expand=True)

        right_frame = ctk.CTkFrame(columns_frame)
        right_frame.pack(side="left", fill="both", padx=(20, 0))

        self._add_metric_section(left_frame, "Annualized Return (10y)", f"{result.annualized_return_10y}%", result.annualized_return_10y_text)
        self._add_metric_section(left_frame, "Beta (to benchmark)", result.beta, result.beta_text)
        self._add_metric_section(left_frame, "Alpha (Jensen's Alpha)", f"{result.alpha}%", result.alpha_text)
        self._add_metric_section(left_frame, "Information Ratio", result.information_ratio, result.information_ratio_text)
        self._add_metric_section(left_frame, "Sharpe Ratio", result.sharpe_ratio, result.sharpe_text)
        self._add_metric_section(left_frame, "Value at Risk (95%, Monthly)", f"{result.var_95}%", result.var_text)
        self._add_metric_section(left_frame, "Conditional VaR (95%, Monthly)", f"{result.cvar_95}%", result.cvar_text)
        self._add_metric_section(left_frame, "Maximum Drawdown", f"{result.max_drawdown}%", result.max_drawdown_text)
        self._add_metric_section(left_frame, "Max Drawdown Duration", f"{result.max_drawdown_duration_days} days", result.max_drawdown_duration_text)
        self._add_metric_section(left_frame, "Diversification Ratio", result.diversification_ratio, result.diversification_text)
        self._add_metric_section(left_frame, "Effective Independent Bets", result.effective_bets, result.effective_bets_text)
        self._add_copy_button(left_frame)

        self._add_risk_contribution_table(right_frame, result)

    def _create_scrollable_frame(self) -> ctk.CTkScrollableFrame:
        scrollable = ctk.CTkScrollableFrame(self.window)
        scrollable.pack(fill="both", expand=True)
        return scrollable

    def _add_header(self, parent: ctk.CTkFrame, text: str):
        label = ctk.CTkLabel(parent, text=text, font=("Arial", 16, "bold"))
        label.pack(anchor="w", padx=15, pady=(15, 5))
        ctk.CTkFrame(parent, height=2, fg_color=("gray75", "gray30")).pack(fill="x", padx=15, pady=(0, 10))

    def _add_metric_section(self, parent: ctk.CTkFrame, name: str, value, description: str):
        self._metrics.append((name, str(value)))
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", padx=15, pady=(5, 0))
        ctk.CTkLabel(frame, text=f"{name}:  ", font=("Arial", 11, "bold")).pack(side="left")
        ctk.CTkLabel(frame, text=str(value), font=("Arial", 11)).pack(side="left")
        desc_label = ctk.CTkLabel(parent, text=description, wraplength=450, justify="left", text_color=("gray35", "gray75"))
        desc_label.pack(anchor="w", padx=25, pady=(0, 8))

    def _add_risk_contribution_table(self, parent: ctk.CTkFrame, result: AnalysisResult):
        self._add_section_label(parent, "Risk & Return Contribution Breakdown")
        desc = ctk.CTkLabel(parent, text=result.risk_contributions_text, wraplength=450, justify="left", text_color=("gray35", "gray75"))
        desc.pack(anchor="w", padx=25, pady=(0, 2))
        desc2 = ctk.CTkLabel(parent, text=result.return_contributions_text, wraplength=450, justify="left", text_color=("gray35", "gray75"))
        desc2.pack(anchor="w", padx=25, pady=(0, 5))

        columns = ("ticker", "risk", "weight", "return")
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=min(len(result.risk_contributions), 12))
        for col, label in [
            ("ticker", "Ticker"),
            ("risk", "Risk Contribution %"),
            ("weight", "Portfolio Weight %"),
            ("return", "Return Contribution %"),
        ]:
            tree.heading(col, text=label, command=lambda c=col: self._sort_treeview(tree, c))
        tree.column("ticker", width=150)
        tree.column("risk", width=160)
        tree.column("weight", width=150)
        tree.column("return", width=170)

        for ticker, risk_pct in sorted(result.risk_contributions.items(), key=lambda x: -x[1]):
            ret_pct = result.return_contributions.get(ticker, 0.0)
            weight_pct = result.portfolio_weights[ticker]
            tree.insert(
                "", "end",
                values=(ticker, f"{risk_pct:.1f}%", f"{weight_pct:.1f}%", f"{ret_pct:.2f}%"),
            )
        tree.pack(padx=25, pady=(0, 15))
        self._sort_ascending: dict[str, bool] = {}

    def _sort_treeview(self, tree: ttk.Treeview, column: str):
        """Sort treeview rows by the clicked column, toggling ascending/descending."""
        ascending = not self._sort_ascending.get(column, False)
        self._sort_ascending[column] = ascending

        rows = [(tree.set(iid, column), iid) for iid in tree.get_children()]
        if column != "ticker":
            rows.sort(key=lambda r: float(r[0].strip('%')), reverse=not ascending)
        else:
            rows.sort(key=lambda r: r[0], reverse=not ascending)

        for index, (_, iid) in enumerate(rows):
            tree.move(iid, "", index)

    def _add_copy_button(self, parent: ctk.CTkFrame):
        btn = ctk.CTkButton(
            parent, text="Copy to Clipboard",
            command=self._copy_metrics_to_clipboard
        )
        btn.pack(anchor="w", padx=15, pady=(10, 10))

    def _copy_metrics_to_clipboard(self):
        lines = [f"{name}: {value}" for name, value in self._metrics]
        text = "\n".join(lines)
        self.window.clipboard_clear()
        self.window.clipboard_append(text)

    def _add_section_label(self, parent: ctk.CTkFrame, text: str):
        ctk.CTkFrame(parent, height=2, fg_color=("gray75", "gray30")).pack(fill="x", padx=15, pady=(10, 5))
        label = ctk.CTkLabel(parent, text=text, font=("Arial", 11, "bold"))
        label.pack(anchor="w", padx=15, pady=(0, 3))
