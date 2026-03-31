from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox as msgbox

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from backend.backend import BackEnd
    from backend.portfolio.portfolio_analyzer import AnalysisResult


class AnalyzePortfolioWindow:
    """Popup window that displays advanced portfolio risk/return metrics."""

    def __init__(self, master, backend: BackEnd):
        self.backend = backend
        self.window = tk.Toplevel(master)
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
        canvas, scrollable = self._create_scrollable_frame()
        self._add_header(scrollable, "Portfolio Analysis")

        columns_frame = tk.Frame(scrollable)
        columns_frame.pack(fill="both", expand=True, padx=5)

        left_frame = tk.Frame(columns_frame)
        left_frame.pack(side="left", fill="both", expand=True)

        right_frame = tk.Frame(columns_frame)
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

    def _add_metric_section(self, parent: tk.Frame, name: str, value, description: str):
        self._metrics.append((name, str(value)))
        frame = tk.Frame(parent)
        frame.pack(fill="x", padx=15, pady=(5, 0))
        tk.Label(frame, text=f"{name}:  ", font=("Arial", 11, "bold")).pack(side="left")
        tk.Label(frame, text=str(value), font=("Arial", 11)).pack(side="left")
        desc_label = tk.Label(parent, text=description, wraplength=450, justify="left", fg="#555555")
        desc_label.pack(anchor="w", padx=25, pady=(0, 8))

    def _add_risk_contribution_table(self, parent: tk.Frame, result: AnalysisResult):
        self._add_section_label(parent, "Risk & Return Contribution Breakdown")
        desc = tk.Label(parent, text=result.risk_contributions_text, wraplength=450, justify="left", fg="#555555")
        desc.pack(anchor="w", padx=25, pady=(0, 2))
        desc2 = tk.Label(parent, text=result.return_contributions_text, wraplength=450, justify="left", fg="#555555")
        desc2.pack(anchor="w", padx=25, pady=(0, 5))

        columns = ("ticker", "risk", "return")
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=min(len(result.risk_contributions), 12))
        for col, label in [("ticker", "Ticker"), ("risk", "Risk Contribution %"), ("return", "Return Contribution %")]:
            tree.heading(col, text=label, command=lambda c=col: self._sort_treeview(tree, c))
        tree.column("ticker", width=150)
        tree.column("risk", width=160)
        tree.column("return", width=170)

        for ticker, risk_pct in sorted(result.risk_contributions.items(), key=lambda x: -x[1]):
            ret_pct = result.return_contributions.get(ticker, 0.0)
            tree.insert("", "end", values=(ticker, f"{risk_pct:.1f}%", f"{ret_pct:.2f}%"))
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

    def _add_copy_button(self, parent: tk.Frame):
        btn = tk.Button(
            parent, text="Copy to Clipboard",
            command=self._copy_metrics_to_clipboard
        )
        btn.pack(anchor="w", padx=15, pady=(10, 10))

    def _copy_metrics_to_clipboard(self):
        lines = [f"{name}: {value}" for name, value in self._metrics]
        text = "\n".join(lines)
        self.window.clipboard_clear()
        self.window.clipboard_append(text)

    def _add_section_label(self, parent: tk.Frame, text: str):
        separator = ttk.Separator(parent, orient="horizontal")
        separator.pack(fill="x", padx=15, pady=(10, 5))
        label = tk.Label(parent, text=text, font=("Arial", 11, "bold"))
        label.pack(anchor="w", padx=15, pady=(0, 3))
