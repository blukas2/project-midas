from __future__ import annotations

import tkinter as tk
from tkinter import messagebox as msgbox

from matplotlib import pyplot
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from backend.backend import BackEnd

class CompareWindow:
    def __init__(self, master, backend: BackEnd):
        self.window = tk.Toplevel(master)
        self.window.title("Compare assets")
        self.backend = backend
        self.chart_dpi = 80
        self._define_components()
        self._place_components()


    def _define_components(self):
        self.lbl_asset1_title = tk.Label(self.window, text="Asset 1: ") 
        self.lbl_asset2_title = tk.Label(self.window, text="Asset 2: ")
        self.entry_asset1_ticker = tk.Entry(self.window, width = 10, borderwidth = 5)
        self.entry_asset2_ticker = tk.Entry(self.window, width = 10, borderwidth = 5)
        self.btn_compare = tk.Button(self.window,text ="Compare!", command = self.compare)

    def _place_components(self):
        self.lbl_asset1_title.grid(row = 1, column = 1, columnspan = 1)
        self.lbl_asset2_title.grid(row = 1, column = 3, columnspan = 1)
        self.entry_asset1_ticker.grid(row = 1, column = 2, columnspan = 1)
        self.entry_asset2_ticker.grid(row = 1, column = 4, columnspan = 1)
        self.btn_compare.grid(row = 2, column = 2, columnspan = 2)

    def compare(self):
        asset1_ticker = self._read_ticker(self.entry_asset1_ticker, 'Asset 1')
        asset2_ticker = self._read_ticker(self.entry_asset2_ticker, 'Asset 2')
        if (asset1_ticker is not None) and (asset2_ticker is not None):
            try:
                self.backend.comparer.compare(asset1_ticker, asset2_ticker)
            except AttributeError:
                msgbox.showerror(title="ERROR!", message='No data found, on of the symbols may be delisted.')
            else:
                self._display_asset_names()
                self._plot_history_comparison()
                self._plot_annualized_returns_asset1()
                self._plot_annualized_returns_asset2()

    def _read_ticker(self, entry: tk.Entry, entry_name):
        try:
            ticker = str(entry.get())
        except ValueError:
            msgbox.showerror(title="ERROR!", message=f"Invalid ticker or quantity for '{entry_name}'.")
        else:
            return ticker
        
    def _display_asset_names(self):
        self.lbl_asset1_name = tk.Label(self.window, text=self.backend.comparer.asset1_name)
        self.lbl_asset1_name.grid(row = 3, column = 1, columnspan = 2)
        self.lbl_asset2_name = tk.Label(self.window, text=self.backend.comparer.asset2_name)
        self.lbl_asset2_name.grid(row = 3, column = 3, columnspan = 2)

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
        self.main_plot_canvas.get_tk_widget().grid(row = 4, column = 1, columnspan = 4)

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
        self.annualized_returns_plot_canvas_asset1.get_tk_widget().grid(row = 5, column = 1, columnspan = 2)

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
        self.annualized_returns_plot_canvas_asset1.get_tk_widget().grid(row = 5, column = 3, columnspan = 2)

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
