from __future__ import annotations

import tkinter as tk
from tkinter import messagebox as msgbox

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from backend.backend import BackEnd
    from ui.main_window.main_window import MainWindowComponents


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


class OpenPortfolioWindow:
    def __init__(self, master, backend: BackEnd, main_window: MainWindowComponents):
        self.backend = backend
        self.main_window = main_window
        self.window = tk.Toplevel(master)
        self.window.title("Opening Portfolio...")
        self._define_components()
        self._place_components()

    def _define_components(self):
        self.lbl_maintext = tk.Label(self.window, text="Select Portfolio")
        ##################
        self.dropd_content = tk.StringVar()
        if self.backend.file_manager.portfolio_names_list:
            self.dropd_content.set(self.backend.file_manager.portfolio_names_list[0])
        self.dropd_selecter = tk.OptionMenu(self.window, self.dropd_content , *self.backend.file_manager.portfolio_names_list)
        
        self.btn_ok = tk.Button(self.window, text ="OK", command=self.load_selected_portfolio)
        self.btn_cancel = tk.Button(self.window,text ="Cancel", command = self.close)

    def _place_components(self):
        self.lbl_maintext.grid(row = 1, column = 1, columnspan = 2)
        self.dropd_selecter.grid(row = 2, column = 1, columnspan = 2)
        self.btn_ok.grid(row = 3, column = 1, columnspan = 1)
        self.btn_cancel.grid(row = 3, column = 2, columnspan = 1)

    def close(self):
        self.window.destroy()

    def load_selected_portfolio(self):
        portfolio_name = self.dropd_content.get()
        self.backend.load_portfolio(portfolio_name)
        self.main_window.recalculate_portfolio()
        self.window.destroy()


class NewPortfolioWindow:
    def __init__(self, master, backend: BackEnd, main_window: MainWindowComponents):
        self.backend = backend
        self.main_window = main_window
        self.window = tk.Toplevel(master)
        self.window.title("Creating New Portfolio...")
        self._define_components()
        self._place_components()

    def _define_components(self):
        self.lbl_portfolio_name = tk.Label(self.window, text="Portfolio name:")
        self.entry_portfolio_name = tk.Entry(self.window, width = 10, borderwidth = 5)
        
        self.btn_ok = tk.Button(self.window,text ="OK", command=self.new_portfolio)
        self.btn_cancel = tk.Button(self.window,text ="Cancel", command = self.close)

    def _place_components(self):
        self.lbl_portfolio_name.grid(row = 1, column = 1, columnspan = 1)
        self.entry_portfolio_name.grid(row = 1, column = 2, columnspan = 1)

        self.btn_ok.grid(row = 2, column = 1, columnspan = 1)
        self.btn_cancel.grid(row = 2, column = 2, columnspan = 1)

    def close(self):
        self.window.destroy()

    def new_portfolio(self):                
        try:
            portfolio_name = str(self.entry_portfolio_name.get())
        except ValueError:
            msgbox.showerror(title="ERROR!", message='Invalid ticker or quantity.')
        else:
            self.backend.file_manager.list_portfolio_names()
            if portfolio_name in self.backend.file_manager.portfolio_names_list:
                msgbox.showerror(title="ERROR!", message=f"Portfolio under the name '{portfolio_name}' already exists!")
            else:
                self.backend.new_portfolio(portfolio_name)
                self.main_window.display_portfolio_name()
                self.window.destroy()
