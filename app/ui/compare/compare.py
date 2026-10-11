from __future__ import annotations

import tkinter as tk
import customtkinter as ctk

from ui.assets.find_asset import FindAssetForCompareWindow
from ui.charts.figure_factory import FigureFactory
from ui.charts.page_builder import ChartCardSpec
from ui.charts.plotly_dashboard import PlotlyDashboard
from ui.dialogs import ThemedMessageBox as msgbox

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from backend.backend import BackEnd

class CompareWindow:
    def __init__(self, master, backend: BackEnd):
        self.window = ctk.CTkToplevel(master)
        self.window.title("Compare assets")
        self.window.geometry("1100x850")
        self.backend = backend
        self.chart_factory = FigureFactory()
        self._use_portfolio_for_asset1 = False
        self._use_portfolio_for_asset2 = False
        self._show_in_eur = True
        self._comparison_done = False
        self._define_components()
        self._place_components()

    def _define_components(self):
        self._define_asset_controls()
        self._define_currency_control()
        self._define_chart_dashboard()

    def _define_asset_controls(self):
        self.lbl_asset1_title = ctk.CTkLabel(self.window, text="Asset 1: ")
        self.lbl_asset2_title = ctk.CTkLabel(self.window, text="Asset 2: ")
        self.entry_asset1_ticker = ctk.CTkEntry(self.window, width=150)
        self.entry_asset2_ticker = ctk.CTkEntry(self.window, width=150)
        self.btn_find_asset1 = ctk.CTkButton(self.window, text="Find Asset", command=self._open_find_asset1)
        self.btn_find_asset2 = ctk.CTkButton(self.window, text="Find Asset", command=self._open_find_asset2)
        self.btn_portfolio_asset1 = ctk.CTkButton(self.window, text="Use Portfolio", command=self._use_portfolio_as_asset1)
        self.btn_portfolio_asset2 = ctk.CTkButton(self.window, text="Use Portfolio", command=self._use_portfolio_as_asset2)
        self.btn_compare = ctk.CTkButton(self.window, text="Compare!", command=self.compare)

    def _define_currency_control(self):
        self._currency_var = tk.StringVar(value="EUR")
        self.dropdown_currency = ctk.CTkComboBox(
            self.window,
            variable=self._currency_var,
            values=["EUR", "Local"],
            state="readonly",
            width=160,
            command=self._on_currency_change,
        )

    def _define_chart_dashboard(self):
        cards = [
            ChartCardSpec("comparison-history", "Normalized price history", wide=True),
            ChartCardSpec("comparison-returns", "Annualized returns"),
            ChartCardSpec("comparison-volatility", "Volatility"),
        ]
        self.dashboard = PlotlyDashboard(
            self.window, "Asset comparison", cards, include_metrics=True, height=650
        )

    def _place_components(self):
        self._place_asset_controls()
        self._configure_chart_area()

    def _place_asset_controls(self):
        self.lbl_asset1_title.grid(row=1, column=1)
        self.entry_asset1_ticker.grid(row=1, column=2)
        self.btn_find_asset1.grid(row=1, column=3)
        self.btn_portfolio_asset1.grid(row=1, column=4)
        self.lbl_asset2_title.grid(row=2, column=1)
        self.entry_asset2_ticker.grid(row=2, column=2)
        self.btn_find_asset2.grid(row=2, column=3)
        self.btn_portfolio_asset2.grid(row=2, column=4)
        self.btn_compare.grid(row=3, column=1, columnspan=2)
        self.dropdown_currency.grid(row=3, column=3, columnspan=2)

    def _configure_chart_area(self):
        self.dashboard.grid(row=4, column=1, columnspan=4, sticky="nsew", padx=8, pady=8)
        self.window.rowconfigure(4, weight=1)
        for column in range(1, 5):
            self.window.columnconfigure(column, weight=1)

    def compare(self):
        try:
            self._run_comparison()
        except AttributeError:
            msgbox.showerror(
                title="ERROR!",
                message='No data found, one of the symbols may be delisted.',
                parent=self.window,
            )
        else:
            self._comparison_done = True
            self._show_in_eur = True
            self._currency_var.set("EUR")
            self._display_charts()

    def _on_currency_change(self, event=None):
        if not self._comparison_done:
            return
        self._show_in_eur = self._currency_var.get() == "EUR"
        self.backend.comparer.recalculate(self._show_in_eur)
        self._display_charts()

    def _display_charts(self):
        comparer = self.backend.comparer
        figures = self._comparison_figures(comparer)
        metrics = [("Asset 1", comparer.asset1_name), ("Asset 2", comparer.asset2_name)]
        self.dashboard.render(
            figures, metrics, subtitle=f"Comparison in {self._currency_var.get()}"
        )

    def _comparison_figures(self, comparer):
        mode = ctk.get_appearance_mode()
        return {
            "comparison-history": self._history_figure(comparer, mode),
            "comparison-returns": self._metric_figure(comparer, "annualized_returns", mode),
            "comparison-volatility": self._metric_figure(comparer, "volatility", mode),
        }

    def _history_figure(self, comparer, mode):
        table = comparer.compare_table
        series = self._history_series(comparer, table)
        return self.chart_factory.line_chart(series, mode, "Indexed price (100 = start)")

    def _history_series(self, comparer, table):
        dates = table["Date"].tolist()
        return [
            (comparer.asset1_name, dates, table["asset1_price_index"].tolist()),
            (comparer.asset2_name, dates, table["asset2_price_index"].tolist()),
        ]

    def _metric_figure(self, comparer, metric, mode):
        series = self._comparison_metric_series(comparer, metric)
        axis_title = "Volatility" if metric == "volatility" else "Annualized return"
        return self.chart_factory.grouped_bar_chart(series, mode, axis_title)

    def _comparison_metric_series(self, comparer, metric):
        return [
            (comparer.asset1_name, getattr(comparer, f"asset1_{metric}")),
            (comparer.asset2_name, getattr(comparer, f"asset2_{metric}")),
        ]

    def _run_comparison(self):
        if self._use_portfolio_for_asset1 and self._use_portfolio_for_asset2:
            self._show_invalid_portfolio_selection()
            return
        if self._use_portfolio_for_asset1:
            self._compare_portfolio_and_ticker(self.entry_asset2_ticker, "Asset 2", 1)
        elif self._use_portfolio_for_asset2:
            self._compare_portfolio_and_ticker(self.entry_asset1_ticker, "Asset 1", 2)
        else:
            self._compare_two_tickers()

    def _show_invalid_portfolio_selection(self):
        msgbox.showerror(
            title="ERROR!", message="Cannot use portfolio for both assets.", parent=self.window
        )

    def _compare_portfolio_and_ticker(self, entry, entry_name, position):
        ticker = self._read_ticker(entry, entry_name)
        if ticker is not None:
            self.backend.comparer.compare_with_portfolio(self.backend.portfolio, ticker, position)

    def _compare_two_tickers(self):
        ticker1 = self._read_ticker(self.entry_asset1_ticker, "Asset 1")
        ticker2 = self._read_ticker(self.entry_asset2_ticker, "Asset 2")
        if ticker1 is not None and ticker2 is not None:
            self.backend.comparer.compare(ticker1, ticker2)

    def _read_ticker(self, entry: ctk.CTkEntry, entry_name):
        try:
            ticker = str(entry.get())
        except ValueError:
            msgbox.showerror(
                title="ERROR!",
                message=f"Invalid ticker or quantity for '{entry_name}'.",
                parent=self.window,
            )
        else:
            return ticker
        
    def _use_portfolio_as_asset1(self):
        if not self._is_portfolio_loaded():
            return
        self._use_portfolio_for_asset1 = True
        self._set_entry_to_portfolio_name(self.entry_asset1_ticker)

    def _use_portfolio_as_asset2(self):
        if not self._is_portfolio_loaded():
            return
        self._use_portfolio_for_asset2 = True
        self._set_entry_to_portfolio_name(self.entry_asset2_ticker)

    def _is_portfolio_loaded(self) -> bool:
        if not self.backend.portfolio.content:
            msgbox.showerror(title="ERROR!", message='No portfolio loaded.', parent=self.window)
            return False
        return True

    def _set_entry_to_portfolio_name(self, entry: ctk.CTkEntry):
        name = self.backend.portfolio.name or "Portfolio"
        entry.delete(0, tk.END)
        entry.insert(0, name)
        entry.configure(state="disabled")

    def _open_find_asset1(self):
        self._use_portfolio_for_asset1 = False
        self.entry_asset1_ticker.configure(state='normal')
        FindAssetForCompareWindow(self.window, self.backend, self._prefill_asset1_ticker)

    def _open_find_asset2(self):
        self._use_portfolio_for_asset2 = False
        self.entry_asset2_ticker.configure(state='normal')
        FindAssetForCompareWindow(self.window, self.backend, self._prefill_asset2_ticker)

    def _prefill_asset1_ticker(self, ticker: str):
        self.entry_asset1_ticker.delete(0, tk.END)
        self.entry_asset1_ticker.insert(0, ticker)

    def _prefill_asset2_ticker(self, ticker: str):
        self.entry_asset2_ticker.delete(0, tk.END)
        self.entry_asset2_ticker.insert(0, ticker)
