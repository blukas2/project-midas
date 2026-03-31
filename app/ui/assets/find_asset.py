from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox as msgbox

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from typing import Callable, TYPE_CHECKING
if TYPE_CHECKING:
    from backend.backend import BackEnd


class FindAssetWindow:
    """Window for searching assets, viewing price history and annualized returns."""

    def __init__(self, master, backend: BackEnd):
        self.backend = backend
        self.window = tk.Toplevel(master)
        self.window.title("Find Asset")
        self.chart_dpi = 80
        self.show_in_eur = False
        self.search_results = []
        self._define_search_section()
        self._define_results_section()
        self._define_currency_dropdown()
        self._define_chart_placeholders()
        self._place_components()

    def _define_search_section(self):
        self.lbl_search = tk.Label(self.window, text="Search:")
        self.entry_search = tk.Entry(self.window, width=30, borderwidth=5)
        self.btn_search = tk.Button(self.window, text="Search", command=self._on_search)

    def _define_results_section(self):
        self.lbl_results = tk.Label(self.window, text="Results:")
        self.listbox_results = tk.Listbox(self.window, width=60, height=10)
        self.listbox_results.bind('<<ListboxSelect>>', self._on_select)

    def _define_currency_dropdown(self):
        self._currency_var = tk.StringVar(value="Local")
        self.dropdown_currency = ttk.Combobox(
            self.window, textvariable=self._currency_var,
            values=["Local", "EUR"], state="readonly", width=12
        )
        self.dropdown_currency.bind("<<ComboboxSelected>>", self._on_currency_change)

    def _define_chart_placeholders(self):
        self.price_figure = Figure(figsize=(8, 4), dpi=self.chart_dpi)
        self.price_canvas = FigureCanvasTkAgg(self.price_figure, self.window)
        self.returns_figure = Figure(figsize=(6, 3), dpi=self.chart_dpi)
        self.returns_canvas = FigureCanvasTkAgg(self.returns_figure, self.window)

    def _place_components(self):
        self.lbl_search.grid(row=1, column=1)
        self.entry_search.grid(row=1, column=2, columnspan=2)
        self.btn_search.grid(row=1, column=4)
        self.lbl_results.grid(row=2, column=1, sticky='nw')
        self.listbox_results.grid(row=2, column=2, columnspan=3, pady=5)
        self.dropdown_currency.grid(row=3, column=1, columnspan=2, pady=5)
        self.price_canvas.get_tk_widget().grid(row=4, column=1, columnspan=4)
        self.returns_canvas.get_tk_widget().grid(row=5, column=1, columnspan=4)

    def _on_search(self):
        query = self.entry_search.get().strip()
        if not query:
            return
        try:
            self.search_results = self.backend.asset_analyzer.search(query)
        except Exception:
            msgbox.showerror(title="Error", message="Search failed. Please try again.")
            return
        self._populate_results()

    def _populate_results(self):
        self.listbox_results.delete(0, tk.END)
        for result in self.search_results:
            self.listbox_results.insert(tk.END, str(result))

    def _on_select(self, event):
        selection = self.listbox_results.curselection()
        if not selection:
            return
        selected = self.search_results[selection[0]]
        try:
            self.backend.asset_analyzer.load_asset(selected.ticker)
        except Exception:
            msgbox.showerror(title="Error", message=f"Could not load '{selected.ticker}'.")
            return
        self._update_currency_dropdown()
        self._refresh_charts()

    def _on_currency_change(self, event=None):
        self.show_in_eur = self._currency_var.get() == "EUR"
        self._refresh_charts()

    def _update_currency_dropdown(self):
        native = self.backend.asset_analyzer.native_currency
        current = "EUR" if self.show_in_eur else native
        self.dropdown_currency.config(values=[native, "EUR"])
        self._currency_var.set(current)

    def _refresh_charts(self):
        self._plot_price_history()
        self._plot_annualized_returns()

    def _plot_price_history(self):
        self.price_figure.clear()
        ax = self.price_figure.add_subplot(111)
        df = self.backend.asset_analyzer.get_price_history(self.show_in_eur)
        currency = self.backend.asset_analyzer.get_currency_label(self.show_in_eur)
        df.plot(x='Date', y='Price', kind='line', legend=True, ax=ax)
        ax.set_title(f"Price History ({currency})")
        ax.set_ylabel(currency)
        self.price_canvas.draw()

    def _plot_annualized_returns(self):
        self.returns_figure.clear()
        ax = self.returns_figure.add_subplot(111)
        returns = self.backend.asset_analyzer.get_annualized_returns(self.show_in_eur)
        if returns:
            bar = ax.bar(returns.keys(), returns.values())
            ax.bar_label(bar)
        currency = self.backend.asset_analyzer.get_currency_label(self.show_in_eur)
        ax.set_title(f"Annualized Returns ({currency})")
        ax.set_ylabel('%')
        self.returns_canvas.draw()


class FindAssetForPositionWindow(FindAssetWindow):
    """Find Asset window launched from Change Position, with portfolio overlay."""

    def __init__(self, master, backend: BackEnd, on_select_callback: Callable[[str], None]):
        self.on_select_callback = on_select_callback
        self.selected_ticker: str | None = None
        super().__init__(master, backend)
        self.show_in_eur = True
        self._currency_var.set("EUR")

    def _place_components(self):
        super()._place_components()
        self.btn_select = tk.Button(self.window, text="Select Asset", command=self._select_asset)
        self.btn_cancel = tk.Button(self.window, text="Cancel", command=self._cancel)
        self.btn_select.grid(row=6, column=2, pady=5)
        self.btn_cancel.grid(row=6, column=3, pady=5)

    def _on_select(self, event):
        selection = self.listbox_results.curselection()
        if not selection:
            return
        self.selected_ticker = self.search_results[selection[0]].ticker
        super()._on_select(event)

    def _plot_price_history(self):
        self.price_figure.clear()
        ax = self.price_figure.add_subplot(111)
        analyzer = self.backend.asset_analyzer
        currency = analyzer.get_currency_label(self.show_in_eur)
        if self.show_in_eur:
            self._plot_indexed_price_history(ax)
        else:
            df = analyzer.get_price_history(self.show_in_eur)
            df.plot(x='Date', y='Price', kind='line', legend=True, ax=ax)
        ax.set_title(f"Price History ({currency})")
        self.price_canvas.draw()

    def _plot_indexed_price_history(self, ax):
        """Plot asset and portfolio both indexed to 100."""
        analyzer = self.backend.asset_analyzer
        asset_df = analyzer.get_indexed_price_history(in_eur=True)
        asset_df.plot(x='Date', y='Asset', kind='line', legend=True, ax=ax)
        try:
            portfolio_df = analyzer.get_portfolio_indexed_history(self.backend.portfolio)
            if not portfolio_df.empty:
                portfolio_df.plot(x='Date', y='Portfolio', kind='line', legend=True, ax=ax)
        except AttributeError:
            pass
        ax.set_ylabel('Index (100 = start)')

    def _plot_annualized_returns(self):
        self.returns_figure.clear()
        ax = self.returns_figure.add_subplot(111)
        analyzer = self.backend.asset_analyzer
        currency = analyzer.get_currency_label(self.show_in_eur)
        asset_returns = analyzer.get_annualized_returns(self.show_in_eur)
        if self.show_in_eur:
            self._plot_grouped_annualized_returns(ax, asset_returns)
        else:
            if asset_returns:
                bar = ax.bar(asset_returns.keys(), asset_returns.values())
                ax.bar_label(bar)
        ax.set_title(f"Annualized Returns ({currency})")
        ax.set_ylabel('%')
        self.returns_canvas.draw()

    def _plot_grouped_annualized_returns(self, ax, asset_returns: dict):
        """Plot asset and portfolio annualized returns side by side."""
        try:
            portfolio_returns = self.backend.portfolio.annualized_returns
        except AttributeError:
            portfolio_returns = {}
        periods = list(asset_returns.keys())
        if not periods:
            return
        x = np.arange(len(periods))
        width = 0.35
        asset_vals = [asset_returns.get(p, 0) for p in periods]
        portfolio_vals = [portfolio_returns.get(p, 0) for p in periods]
        bar1 = ax.bar(x - width / 2, asset_vals, width, label='Asset')
        bar2 = ax.bar(x + width / 2, portfolio_vals, width, label='Portfolio')
        ax.bar_label(bar1)
        ax.bar_label(bar2)
        ax.set_xticks(x)
        ax.set_xticklabels(periods)
        ax.legend()

    def _select_asset(self):
        if self.selected_ticker:
            self.on_select_callback(self.selected_ticker)
        self.window.destroy()

    def _cancel(self):
        self.window.destroy()


class FindAssetForCompareWindow(FindAssetWindow):
    """Find Asset window launched from Compare Assets, with Select/Cancel buttons."""

    def __init__(self, master, backend: BackEnd, on_select_callback: Callable[[str], None]):
        self.on_select_callback = on_select_callback
        self.selected_ticker: str | None = None
        super().__init__(master, backend)

    def _place_components(self):
        super()._place_components()
        self.btn_select = tk.Button(self.window, text="Select Asset", command=self._select_asset)
        self.btn_cancel = tk.Button(self.window, text="Cancel", command=self._cancel)
        self.btn_select.grid(row=6, column=2, pady=5)
        self.btn_cancel.grid(row=6, column=3, pady=5)

    def _on_select(self, event):
        selection = self.listbox_results.curselection()
        if not selection:
            return
        self.selected_ticker = self.search_results[selection[0]].ticker
        super()._on_select(event)

    def _select_asset(self):
        if self.selected_ticker:
            self.on_select_callback(self.selected_ticker)
        self.window.destroy()

    def _cancel(self):
        self.window.destroy()
