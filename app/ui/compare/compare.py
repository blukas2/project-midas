from __future__ import annotations

import tkinter as tk
import customtkinter as ctk

from matplotlib import pyplot
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from ui.assets.find_asset import FindAssetForCompareWindow
from ui.dialogs import ThemedMessageBox as msgbox
from ui.theme import style_chart

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from backend.backend import BackEnd

class CompareWindow:
    def __init__(self, master, backend: BackEnd):
        self.window = ctk.CTkToplevel(master)
        self.window.title("Compare assets")
        self.window.geometry("1100x850")
        self.backend = backend
        self.chart_dpi = 80
        self._use_portfolio_for_asset1 = False
        self._use_portfolio_for_asset2 = False
        self._show_in_eur = True
        self._comparison_done = False
        self._define_components()
        self._place_components()


    def _define_components(self):
        self.lbl_asset1_title = ctk.CTkLabel(self.window, text="Asset 1: ")
        self.lbl_asset2_title = ctk.CTkLabel(self.window, text="Asset 2: ")
        self.entry_asset1_ticker = ctk.CTkEntry(self.window, width=150)
        self.entry_asset2_ticker = ctk.CTkEntry(self.window, width=150)
        self.btn_find_asset1 = ctk.CTkButton(self.window, text="Find Asset", command=self._open_find_asset1)
        self.btn_find_asset2 = ctk.CTkButton(self.window, text="Find Asset", command=self._open_find_asset2)
        self.btn_portfolio_asset1 = ctk.CTkButton(self.window, text="Use Portfolio", command=self._use_portfolio_as_asset1)
        self.btn_portfolio_asset2 = ctk.CTkButton(self.window, text="Use Portfolio", command=self._use_portfolio_as_asset2)
        self.btn_compare = ctk.CTkButton(self.window, text="Compare!", command=self.compare)
        self._currency_var = tk.StringVar(value="EUR")
        self.dropdown_currency = ctk.CTkComboBox(
            self.window,
            variable=self._currency_var,
            values=["EUR", "Local"],
            state="readonly",
            width=160,
            command=self._on_currency_change,
        )

    def _place_components(self):
        self.lbl_asset1_title.grid(row = 1, column = 1, columnspan = 1)
        self.entry_asset1_ticker.grid(row = 1, column = 2, columnspan = 1)
        self.btn_find_asset1.grid(row = 1, column = 3, columnspan = 1)
        self.btn_portfolio_asset1.grid(row = 1, column = 4, columnspan = 1)
        self.lbl_asset2_title.grid(row = 2, column = 1, columnspan = 1)
        self.entry_asset2_ticker.grid(row = 2, column = 2, columnspan = 1)
        self.btn_find_asset2.grid(row = 2, column = 3, columnspan = 1)
        self.btn_portfolio_asset2.grid(row = 2, column = 4, columnspan = 1)
        self.btn_compare.grid(row = 3, column = 1, columnspan = 2)
        self.dropdown_currency.grid(row = 3, column = 3, columnspan = 2)

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
        self._display_asset_names()
        self._plot_history_comparison()
        self._plot_annualized_returns_asset1()
        self._plot_annualized_returns_asset2()
        self._plot_volatility_asset1()
        self._plot_volatility_asset2()

    def _run_comparison(self):
        portfolio = self.backend.portfolio
        if self._use_portfolio_for_asset1 and self._use_portfolio_for_asset2:
            msgbox.showerror(title="ERROR!", message='Cannot use portfolio for both assets.', parent=self.window)
            return
        if self._use_portfolio_for_asset1:
            ticker = self._read_ticker(self.entry_asset2_ticker, 'Asset 2')
            if ticker is not None:
                self.backend.comparer.compare_with_portfolio(portfolio, ticker, 1)
        elif self._use_portfolio_for_asset2:
            ticker = self._read_ticker(self.entry_asset1_ticker, 'Asset 1')
            if ticker is not None:
                self.backend.comparer.compare_with_portfolio(portfolio, ticker, 2)
        else:
            asset1 = self._read_ticker(self.entry_asset1_ticker, 'Asset 1')
            asset2 = self._read_ticker(self.entry_asset2_ticker, 'Asset 2')
            if (asset1 is not None) and (asset2 is not None):
                self.backend.comparer.compare(asset1, asset2)

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

    def _display_asset_names(self):
        self.lbl_asset1_name = ctk.CTkLabel(self.window, text=self.backend.comparer.asset1_name)
        self.lbl_asset1_name.grid(row = 4, column = 1, columnspan = 2)
        self.lbl_asset2_name = ctk.CTkLabel(self.window, text=self.backend.comparer.asset2_name)
        self.lbl_asset2_name.grid(row = 4, column = 2, columnspan = 2)

    def _plot_history_comparison(self):
        figure = pyplot.Figure(figsize=(10,4), dpi=self.chart_dpi)
        ax = figure.add_subplot(111)
        self.main_plot_canvas = FigureCanvasTkAgg(figure, self.window)        
        ax.set_title('Price History')
        try:
            df = self.backend.comparer.compare_table[['Date', 'asset1_price_index', 'asset2_price_index']]
        except AttributeError:
            pass
        else:
            df.plot(x='Date', y='asset1_price_index', kind='line', legend=True, ax=ax)
            df.plot(x='Date', y='asset2_price_index', kind='line', legend=True, ax=ax)
        style_chart(figure)
        self.main_plot_canvas.get_tk_widget().grid(row = 5, column = 1, columnspan = 4)

    def _plot_annualized_returns_asset1(self):
        figure = Figure(figsize=(5, 3), dpi=self.chart_dpi)
        self.annualized_returns_plot_canvas_asset1 = FigureCanvasTkAgg(figure, self.window)
        axes = figure.add_subplot()
        try:
            periods = self.backend.comparer.asset1_annualized_returns.keys()
            returns = self.backend.comparer.asset1_annualized_returns.values()
        except AttributeError:
            pass
        else:
            bar = axes.bar(periods, returns)
            axes.set_title('Portfolio Annualized Returns')
            axes.set_ylabel('%')
            axes.bar_label(bar)
            min_limit, max_limit = self._get_y_axes_limits(self.backend.comparer.asset1_annualized_returns, 
                                                           self.backend.comparer.asset2_annualized_returns)
            axes.set_ylim(min_limit, max_limit)
        style_chart(figure)
        self.annualized_returns_plot_canvas_asset1.get_tk_widget().grid(row = 6, column = 1, columnspan = 2)

    def _plot_annualized_returns_asset2(self):
        figure = Figure(figsize=(5, 3), dpi=self.chart_dpi)
        self.annualized_returns_plot_canvas_asset1 = FigureCanvasTkAgg(figure, self.window)
        axes = figure.add_subplot()
        try:
            periods = self.backend.comparer.asset2_annualized_returns.keys()
            returns = self.backend.comparer.asset2_annualized_returns.values()
        except AttributeError:
            pass
        else:
            bar = axes.bar(periods, returns)
            axes.set_title('Portfolio Annualized Returns')
            axes.set_ylabel('%')
            axes.bar_label(bar)
            min_limit, max_limit = self._get_y_axes_limits(self.backend.comparer.asset1_annualized_returns, 
                                                           self.backend.comparer.asset2_annualized_returns)
            axes.set_ylim(min_limit, max_limit)
        style_chart(figure)
        self.annualized_returns_plot_canvas_asset1.get_tk_widget().grid(row = 6, column = 3, columnspan = 2)

    def _plot_volatility_asset1(self):
        figure = Figure(figsize=(5, 3), dpi=self.chart_dpi)
        self.volatility_canvas_asset1 = FigureCanvasTkAgg(figure, self.window)
        axes = figure.add_subplot()
        try:
            periods = self.backend.comparer.asset1_volatility.keys()
            values = self.backend.comparer.asset1_volatility.values()
        except AttributeError:
            pass
        else:
            bar = axes.bar(periods, values)
            axes.set_title('Asset 1 Volatility')
            axes.set_ylabel('%')
            axes.bar_label(bar)
            min_limit, max_limit = self._get_y_axes_limits(
                self.backend.comparer.asset1_volatility,
                self.backend.comparer.asset2_volatility)
            axes.set_ylim(min_limit, max_limit)
        style_chart(figure)
        self.volatility_canvas_asset1.get_tk_widget().grid(row=7, column=1, columnspan=2)

    def _plot_volatility_asset2(self):
        figure = Figure(figsize=(5, 3), dpi=self.chart_dpi)
        self.volatility_canvas_asset2 = FigureCanvasTkAgg(figure, self.window)
        axes = figure.add_subplot()
        try:
            periods = self.backend.comparer.asset2_volatility.keys()
            values = self.backend.comparer.asset2_volatility.values()
        except AttributeError:
            pass
        else:
            bar = axes.bar(periods, values)
            axes.set_title('Asset 2 Volatility')
            axes.set_ylabel('%')
            axes.bar_label(bar)
            min_limit, max_limit = self._get_y_axes_limits(
                self.backend.comparer.asset1_volatility,
                self.backend.comparer.asset2_volatility)
            axes.set_ylim(min_limit, max_limit)
        style_chart(figure)
        self.volatility_canvas_asset2.get_tk_widget().grid(row=7, column=3, columnspan=2)

    def _get_y_axes_limits(self, asset1_data: dict, asset2_data: dict):
        asset1_values = list(asset1_data.values())
        asset2_values = list(asset2_data.values())
        min_limit = min(asset1_values+ asset2_values) * 1.1
        max_limit = max(asset1_values+ asset2_values) * 1.1
        if min_limit > 0:
            min_limit = 0
        if max_limit < 0:
            max_limit = 0
        return min_limit, max_limit
