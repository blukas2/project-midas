from __future__ import annotations

import tkinter as tk
import customtkinter as ctk

from ui.assets.find_asset import FindAssetForPositionWindow
from ui.main_window.analyze_impact import AnalyzeImpactWindow
from ui.dialogs import ThemedMessageBox as msgbox

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from backend.backend import BackEnd
    from ui.main_window.main_window import MainWindowComponents


class ChangePositionWindow:
    def __init__(self, master, subject: MainWindowComponents, backend: BackEnd):
        self.backend = backend
        self.subject = subject
        self.window = ctk.CTkToplevel(master)
        self.window.title("Change Position")
        self.window.geometry("620x130")
        self._define_components()
        self._place_components()

    def _define_components(self):
        self.lbl_ticker = ctk.CTkLabel(self.window, text="Ticker")
        self.entry_ticker = ctk.CTkEntry(self.window, width=150)

        self.lbl_quantity = ctk.CTkLabel(self.window, text="Quantity")
        self.entry_quantity = ctk.CTkEntry(self.window, width=150)
        
        self.btn_find_asset = ctk.CTkButton(self.window, text="Find Asset", command=self._open_find_asset)
        self.btn_change = ctk.CTkButton(self.window, text="Change", command=self.change_position)
        self.btn_analyze_impact = ctk.CTkButton(self.window, text="Analyze Impact", command=self.analyze_impact)
        self.btn_cancel = ctk.CTkButton(self.window, text="Cancel", command=self.close)

    def _place_components(self):
        self.lbl_ticker.grid(row = 1, column = 1, columnspan = 1)
        self.entry_ticker.grid(row = 1, column = 2, columnspan = 1)
        self.lbl_quantity.grid(row = 1, column = 3, columnspan = 1)
        self.entry_quantity.grid(row = 1, column = 4, columnspan = 1)

        self.btn_find_asset.grid(row = 2, column = 1, columnspan = 1)
        self.btn_change.grid(row = 2, column = 2, columnspan = 1)
        self.btn_analyze_impact.grid(row = 2, column = 3, columnspan = 1)
        self.btn_cancel.grid(row = 2, column = 4, columnspan = 1)

    def _open_find_asset(self):
        FindAssetForPositionWindow(self.window, self.backend, self._prefill_ticker)

    def _prefill_ticker(self, ticker: str):
        self.entry_ticker.delete(0, tk.END)
        self.entry_ticker.insert(0, ticker)

    def _validate_inputs(self):
        ticker = self.entry_ticker.get().strip()
        quantity_str = self.entry_quantity.get().strip()
        if not ticker:
            msgbox.showerror(title="ERROR!", message="Please enter a ticker.", parent=self.window)
            return None, None
        try:
            quantity = int(quantity_str)
        except (ValueError, AttributeError):
            msgbox.showerror(title="ERROR!", message="Please enter a valid quantity.", parent=self.window)
            return None, None
        if quantity == 0:
            msgbox.showerror(title="ERROR!", message="Quantity cannot be zero.", parent=self.window)
            return None, None
        return ticker, quantity

    def change_position(self):
        ticker, quantity = self._validate_inputs()
        if ticker is None:
            return
        try:
            self.backend.portfolio.change_position(ticker, quantity)
        except AttributeError:
            msgbox.showerror(title="ERROR!", message=f'{ticker}: No data found, symbol may be delisted.', parent=self.window)
        except ValueError as e:
            msgbox.showerror(title="ERROR!", message=str(e), parent=self.window)
        else:
            self.backend.portfolio.calculate()
            self.subject.refresh_table()
            self.window.destroy()

    def analyze_impact(self):
        ticker, quantity = self._validate_inputs()
        if ticker is None:
            return
        if not self.backend.portfolio.content:
            msgbox.showwarning("No Data", "Portfolio is empty. Add assets first.", parent=self.window)
            return
        try:
            current, projected = self.backend.analyze_impact(ticker, quantity)
        except AttributeError:
            msgbox.showerror(title="ERROR!", message=f'{ticker}: No data found, symbol may be delisted.', parent=self.window)
        except ValueError as e:
            msgbox.showerror(title="ERROR!", message=str(e), parent=self.window)
        except Exception as e:
            msgbox.showerror(title="Analysis Error", message=str(e), parent=self.window)
        else:
            AnalyzeImpactWindow(self.window, current, projected, ticker, quantity)

    def close(self):
        self.window.destroy()


class OpenPortfolioWindow:
    def __init__(self, master, backend: BackEnd, main_window: MainWindowComponents):
        self.backend = backend
        self.main_window = main_window
        self.window = ctk.CTkToplevel(master)
        self.window.title("Opening Portfolio...")
        self.window.geometry("420x180")
        self._define_components()
        self._place_components()

    def _define_components(self):
        self.lbl_maintext = ctk.CTkLabel(self.window, text="Select Portfolio")
        self.dropd_content = tk.StringVar()
        if self.backend.file_manager.portfolio_names_list:
            self.dropd_content.set(self.backend.file_manager.portfolio_names_list[0])
        self.dropd_selecter = ctk.CTkComboBox(
            self.window,
            variable=self.dropd_content,
            values=self.backend.file_manager.portfolio_names_list,
            state="readonly",
            width=260,
        )
        
        self.btn_ok = ctk.CTkButton(self.window, text="OK", command=self.load_selected_portfolio)
        self.btn_cancel = ctk.CTkButton(self.window, text="Cancel", command=self.close)

    def _place_components(self):
        self.lbl_maintext.grid(row = 1, column = 1, columnspan = 2)
        self.dropd_selecter.grid(row = 2, column = 1, columnspan = 2)
        self.btn_ok.grid(row = 3, column = 1, columnspan = 1)
        self.btn_cancel.grid(row = 3, column = 2, columnspan = 1)

    def close(self):
        self.window.destroy()

    def load_selected_portfolio(self):
        portfolio_name = self.dropd_content.get()
        if not portfolio_name:
            return
        self.backend.load_portfolio(portfolio_name)
        self.main_window.recalculate_portfolio()
        self.window.destroy()


class NewPortfolioWindow:
    def __init__(self, master, backend: BackEnd, main_window: MainWindowComponents):
        self.backend = backend
        self.main_window = main_window
        self.window = ctk.CTkToplevel(master)
        self.window.title("Creating New Portfolio...")
        self.window.geometry("420x150")
        self._define_components()
        self._place_components()

    def _define_components(self):
        self.lbl_portfolio_name = ctk.CTkLabel(self.window, text="Portfolio name:")
        self.entry_portfolio_name = ctk.CTkEntry(self.window, width=220)
        
        self.btn_ok = ctk.CTkButton(self.window, text="OK", command=self.new_portfolio)
        self.btn_cancel = ctk.CTkButton(self.window, text="Cancel", command=self.close)

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
            msgbox.showerror(title="ERROR!", message='Invalid ticker or quantity.', parent=self.window)
        else:
            self.backend.file_manager.list_portfolio_names()
            if portfolio_name in self.backend.file_manager.portfolio_names_list:
                msgbox.showerror(
                    title="ERROR!",
                    message=f"Portfolio under the name '{portfolio_name}' already exists!",
                    parent=self.window,
                )
            else:
                self.backend.new_portfolio(portfolio_name)
                self.main_window.display_portfolio_name()
                self.window.destroy()
