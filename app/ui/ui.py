from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox as msgbox

from matplotlib import pyplot
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import pandas as pd
from pandastable import Table, config

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from components.components import BackEnd

class DropdownMenu:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.menu = tk.Menu(self.root)
        root.config(menu=self.menu)
        
        self.portfolio_menu = tk.Menu(self.menu)
        self.menu.add_cascade(label='Portfolio', menu=self.portfolio_menu)
        self.portfolio_menu.add_command(label="New")
        self.portfolio_menu.add_command(label="Open")
        self.portfolio_menu.add_command(label="Save")
        self.portfolio_menu.add_command(label="Save as...")
        self.portfolio_menu.add_command(label="Exit", command=self._exit_command)

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

    def _place_components(self):
        self.btn_change_position.grid(row = 1, column = 1, columnspan = 1)
        self.btn_recalculate_portfolio.grid(row = 1, column = 3, columnspan = 1)
        self.btn_load_portfolio.grid(row = 1, column = 6, columnspan = 1)
        self.btn_save_portfolio.grid(row = 1, column = 7, columnspan = 1)
        self.asset_table.grid(row = 2, column = 1, columnspan = 5)

    def _define_buttons(self):
        self.btn_change_position = tk.Button(self.window, text="Change Position", command=self.change_position)
        self.btn_recalculate_portfolio = tk.Button(self.window, text="Recalculate Portfolio", command=self.recalculate_portfolio)
        self.btn_load_portfolio = tk.Button(self.window, text="Load Portfolio", command=self.load_portfolio)
        self.btn_save_portfolio = tk.Button(self.window, text="Save Portfolio", command=self.save_portfolio)

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
        #pt.show()
        #set some options
        options = {'colheadercolor':'green','floatprecision': 3}
        config.apply_options(options, pt)
        pt.show()

    def change_position(self):
        self.change_position_window = ChangePositionWindow(self.window, self, self.backend)

    def recalculate_portfolio(self):
        self.backend.portfolio.calculate()
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
    
    def load_portfolio(self):
        self.backend.load_portfolio()
        self.recalculate_portfolio()

    def save_portfolio(self):
        self.backend.file_manager.save_portfolio()

class ChangePositionWindow:
    def __init__(self, master, subject: MainWindowComponents, backend: BackEnd):
        self.backend = backend
        self.subject = subject
        self.window = tk.Toplevel(master)
        self.window.title("Change Position")
        self._define_components()
        self._place_components()

    def _define_components(self):
        self.lbl_ticker = tk.Label(self.window, text="Ticker")
        self.entry_ticker = tk.Entry(self.window, width = 10, borderwidth = 5)

        self.lbl_quantity = tk.Label(self.window, text="Quantity")
        self.entry_quantity = tk.Entry(self.window, width = 10, borderwidth = 5)
        
        self.btn_add = tk.Button(self.window,text ="Add", command = self.add_asset)
        self.btn_remove = tk.Button(self.window,text ="Reduce", command=self.reduce_position)
        self.btn_cancel = tk.Button(self.window,text ="Cancel", command = self.close)

    def _place_components(self):
        self.lbl_ticker.grid(row = 1, column = 1, columnspan = 1)
        self.entry_ticker.grid(row = 1, column = 2, columnspan = 1)
        self.lbl_quantity.grid(row = 1, column = 3, columnspan = 1)
        self.entry_quantity.grid(row = 1, column = 4, columnspan = 1)

        self.btn_add.grid(row = 2, column = 2, columnspan = 1)
        self.btn_remove.grid(row = 2, column = 3, columnspan = 1)
        self.btn_cancel.grid(row = 2, column = 4, columnspan = 1)

    def add_asset(self):
        try:
            ticker = str(self.entry_ticker.get())
            quantity = int(self.entry_quantity.get())
        except (ValueError, AttributeError):
            msgbox.showerror(title="ERROR!", message='Invalid ticker or quantity.')
        else:
            try:
                self.backend.portfolio.add_asset(ticker, quantity)
            except AttributeError:
                msgbox.showerror(title="ERROR!", message=f'{ticker}: No data found, symbol may be delisted.')
            else:
                self.backend.portfolio.calculate()
                self.subject.refresh_table()
                self.window.destroy()

    def reduce_position(self):
        try:
            ticker = str(self.entry_ticker.get())
            quantity = int(self.entry_quantity.get())
        except (ValueError, AttributeError):
            msgbox.showerror(title="ERROR!", message='Invalid ticker or quantity.')
        else:
            response_message = self.backend.portfolio.reduce_position(ticker, quantity)
            if response_message is not None:
                msgbox.showerror(title="ERROR!", message=response_message)
            else:
                self.backend.portfolio.calculate()
                self.subject.refresh_table()
                self.window.destroy()

    def close(self):
        self.window.destroy()
