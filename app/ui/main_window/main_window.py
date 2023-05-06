from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from matplotlib import pyplot
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import pandas as pd
from pandastable import Table, config

from ui.main_window.popups import *

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from components.components import BackEnd


class DropdownMenu:
    def __init__(self, root: tk.Tk, backend: BackEnd, main_window: MainWindowComponents):
        self.root = root
        self.menu = tk.Menu(self.root)
        self.main_window = main_window
        self.backend = backend
        root.config(menu=self.menu)
        
        self.portfolio_menu = tk.Menu(self.menu)
        self.menu.add_cascade(label='Portfolio', menu=self.portfolio_menu)
        self.portfolio_menu.add_command(label="New", command=self._new_portfolio)
        self.portfolio_menu.add_command(label="Open", command=self._open_portfolio)
        self.portfolio_menu.add_command(label="Save", command=self._save_portfolio)
        self.portfolio_menu.add_command(label="Exit", command=self._exit_command)

    def _open_portfolio(self):
        self.backend.file_manager.list_portfolio_names()
        self.open_portfolio_window = OpenPortfolioWindow(self.root, self.backend, self.main_window)

    def _save_portfolio(self):
        self.backend.save_portfolio()

    def _new_portfolio(self):
        NewPortfolioWindow(self.root, self.backend, self.main_window)

    def _exit_command(self):
        self.root.destroy()


class MainWindowComponents:
    def __init__(self, window, backend: BackEnd):
        self.window = window
        self.backend = backend
        self._define_buttons()
        self._define_asset_table()
        self.plot_history()
        self.plot_returns()
        self.plot_annualized_returns()
        self.plot_correlation_matrix()
        self._place_components()
        self.display_portfolio_name()

    def _place_components(self):
        self.btn_change_position.grid(row = 1, column = 3, columnspan = 1)
        self.btn_recalculate_portfolio.grid(row = 1, column = 4, columnspan = 1)
        self.asset_table.grid(row = 2, column = 1, columnspan = 5)

    def _define_buttons(self):
        self.btn_change_position = tk.Button(self.window, text="Change Position", command=self.change_position)
        self.btn_recalculate_portfolio = tk.Button(self.window, text="Recalculate Portfolio", command=self.recalculate_portfolio)

    def display_portfolio_name(self):
        text = f"Portfolio name: {self.backend.portfolio.name}"
        self.lbl_portfolio_name = tk.Label(self.window, text=text)
        self.lbl_portfolio_name.grid(row=1, column=1, columnspan=2)

    def _define_asset_table(self):
        self.asset_table = ttk.Treeview(self.window)
        self.asset_table['columns'] = ('ticker', 'name', 'quantity', 'current_price', 'value')        

        self.asset_table.column("#0", width=0,  stretch='NO')
        self.asset_table.column("ticker",width=80)
        self.asset_table.column("name",width=80)
        self.asset_table.column("quantity",width=80)
        self.asset_table.column("current_price",width=80)
        self.asset_table.column("value",width=80)

        self.asset_table.heading("#0",text="")
        self.asset_table.heading("ticker",text='Ticker')
        self.asset_table.heading("name",text='Name')
        self.asset_table.heading("quantity",text='Quantity')
        self.asset_table.heading("current_price",text='Current Price')
        self.asset_table.heading("value",text='Value')

    def plot_history(self):
        figure = pyplot.Figure(figsize=(6,4), dpi=100)
        ax = figure.add_subplot(111)
        self.main_plot_canvas = FigureCanvasTkAgg(figure, self.window)        
        ax.set_title('Value History')
        try:
            df = self.backend.portfolio.history[['Date', 'Value']]
        except AttributeError:
            pass
        else:
            df.plot(x='Date', y='Value', kind='line', legend=True, ax=ax)
        self.main_plot_canvas.get_tk_widget().grid(row = 2, column = 6, columnspan = 4)

    def plot_returns(self):
        figure = Figure(figsize=(6, 3), dpi=100)
        self.returns_plot_canvas = FigureCanvasTkAgg(figure, self.window)
        axes = figure.add_subplot()
        try:
            periods = self.backend.portfolio.returns.keys()
            returns = self.backend.portfolio.returns.values()
        except AttributeError:
            pass
        else:
            bar = axes.bar(periods, returns)
            axes.set_title('Portfolio Returns')
            axes.set_ylabel('%')
            axes.bar_label(bar)
        self.returns_plot_canvas.get_tk_widget().grid(row = 3, column = 6, columnspan = 4)

    def plot_annualized_returns(self):
        figure = Figure(figsize=(6, 3), dpi=100)
        self.annualized_returns_plot_canvas = FigureCanvasTkAgg(figure, self.window)
        axes = figure.add_subplot()
        try:
            periods = self.backend.portfolio.annualized_returns.keys()
            returns = self.backend.portfolio.annualized_returns.values()
        except AttributeError:
            pass
        else:
            bar = axes.bar(periods, returns)
            axes.set_title('Portfolio Annualized Returns')
            axes.set_ylabel('%')
            axes.bar_label(bar)
        self.annualized_returns_plot_canvas.get_tk_widget().grid(row = 3, column = 11, columnspan = 4)

    def plot_correlation_matrix(self):
        f = tk.Frame(self.window)
        f.grid(row = 2, column = 11, columnspan = 4)
        try:
            df = self.backend.portfolio.correlation_matrix
        except AttributeError:
            df = pd.DataFrame()
        self.table = pt = Table(f, dataframe=df,
                                showtoolbar=True, showstatusbar=True)
        options = {'colheadercolor':'green','floatprecision': 3}
        config.apply_options(options, pt)
        pt.show()

    def change_position(self):
        self.change_position_window = ChangePositionWindow(self.window, self, self.backend)

    def recalculate_portfolio(self):
        self.backend.portfolio.calculate()
        self.display_portfolio_name()
        self.refresh_table()
        self.plot_history()
        self.plot_returns()
        self.plot_annualized_returns()
        self.plot_correlation_matrix()

    def refresh_table(self):
        self.asset_table.delete(*self.asset_table.get_children())
        for asset in self.backend.portfolio.content.values():
            iid = len(self.asset_table.get_children())
            self.asset_table.insert(parent='',index='end',iid=iid,text='',
                                    values=(asset.ticker,
                                            asset.info['longName'],
                                            asset.quantity,
                                            asset.info['regularMarketPreviousClose'],
                                            asset.info['regularMarketPreviousClose']*asset.quantity))
