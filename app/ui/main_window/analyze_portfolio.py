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
        self.window.geometry("720x700")
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
        canvas, scrollable = self._create_scrollable_frame()
        self._add_header(scrollable, "Portfolio Analysis")
        self._add_metric_section(scrollable, "Beta (to benchmark)", result.beta, result.beta_text)
        self._add_metric_section(scrollable, "Alpha (Jensen's Alpha)", f"{result.alpha}%", result.alpha_text)
        self._add_metric_section(scrollable, "Sharpe Ratio", result.sharpe_ratio, result.sharpe_text)
        self._add_metric_section(scrollable, "Value at Risk (95%, Monthly)", f"{result.var_95}%", result.var_text)
        self._add_metric_section(scrollable, "Diversification Ratio", result.diversification_ratio, result.diversification_text)
        self._add_metric_section(scrollable, "Effective Independent Bets", result.effective_bets, result.effective_bets_text)
        self._add_risk_contribution_table(scrollable, result)
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
        frame = tk.Frame(parent)
        frame.pack(fill="x", padx=15, pady=(5, 0))
        tk.Label(frame, text=f"{name}:  ", font=("Arial", 11, "bold")).pack(side="left")
        tk.Label(frame, text=str(value), font=("Arial", 11)).pack(side="left")
        desc_label = tk.Label(parent, text=description, wraplength=650, justify="left", fg="#555555")
        desc_label.pack(anchor="w", padx=25, pady=(0, 8))

    def _add_risk_contribution_table(self, parent: tk.Frame, result: AnalysisResult):
        self._add_section_label(parent, "Risk Contribution Breakdown")
        desc = tk.Label(parent, text=result.risk_contributions_text, wraplength=650, justify="left", fg="#555555")
        desc.pack(anchor="w", padx=25, pady=(0, 5))

        tree = ttk.Treeview(parent, columns=("ticker", "contribution"), show="headings", height=min(len(result.risk_contributions), 12))
        tree.heading("ticker", text="Ticker")
        tree.heading("contribution", text="Risk Contribution %")
        tree.column("ticker", width=200)
        tree.column("contribution", width=200)

        for ticker, pct in sorted(result.risk_contributions.items(), key=lambda x: -x[1]):
            tree.insert("", "end", values=(ticker, f"{pct:.1f}%"))
        tree.pack(padx=25, pady=(0, 15))

    def _add_section_label(self, parent: tk.Frame, text: str):
        separator = ttk.Separator(parent, orient="horizontal")
        separator.pack(fill="x", padx=15, pady=(10, 5))
        label = tk.Label(parent, text=text, font=("Arial", 11, "bold"))
        label.pack(anchor="w", padx=15, pady=(0, 3))
