from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import customtkinter as ctk

from matplotlib import pyplot
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import pandas as pd
from pandastable import Table, config

from ui.main_window.popups import *
from ui.main_window.analyze_portfolio import AnalyzePortfolioWindow
from ui.compare.compare import CompareWindow
from ui.assets.find_asset import FindAssetWindow
from ui.theme import style_chart, toggle_appearance_mode

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from backend.backend import BackEnd


class DropdownMenu:
    def __init__(self, root: tk.Tk, backend: BackEnd, main_window: MainWindowComponents):
        self.root = root
        self.main_window = main_window
        self.backend = backend
        self.menu_frame = ctk.CTkFrame(root, corner_radius=0)
        self.menu_frame.grid(row=0, column=0, columnspan=20, sticky="ew")
        self._define_portfolio_menu()
        self._define_assets_menu()
        self._define_analysis_menu()
        self.theme_button = ctk.CTkButton(
            self.menu_frame,
            text=f"Theme: {ctk.get_appearance_mode()}",
            command=self._toggle_theme,
        )
        self.theme_button.pack(side="right", padx=8, pady=6)

    def _define_portfolio_menu(self):
        self.portfolio_menu = self._create_menu("Portfolio")
        self.portfolio_menu.add_command(label="New", command=self._new_portfolio)
        self.portfolio_menu.add_command(label="Open", command=self._open_portfolio)
        self.portfolio_menu.add_command(label="Save", command=self._save_portfolio)
        self.portfolio_menu.add_command(label="Exit", command=self._exit_command)

    def _define_analysis_menu(self):
        self.analysis_menu = self._create_menu("Analysis")
        self.analysis_menu.add_command(label="Compare", command=self._compare_assets)

    def _define_assets_menu(self):
        self.assets_menu = self._create_menu("Assets")
        self.assets_menu.add_command(label="Find Asset...", command=self._find_asset)

    def _create_menu(self, title: str):
        menu = tk.Menu(self.root, tearoff=False)
        button = ctk.CTkButton(
            self.menu_frame,
            text=f"{title}  ▾",
            command=lambda: self._show_menu(menu, button),
        )
        button.pack(side="left", padx=(8, 0), pady=6)
        return menu

    def _show_menu(self, menu, button):
        menu.tk_popup(button.winfo_rootx(), button.winfo_rooty() + button.winfo_height())
        menu.grab_release()

    def _toggle_theme(self):
        mode = toggle_appearance_mode()
        self.main_window.refresh_theme()
        self.theme_button.configure(text=f"Theme: {mode}")

    def _open_portfolio(self):
        self.backend.file_manager.list_portfolio_names()
        self.open_portfolio_window = OpenPortfolioWindow(self.root, self.backend, self.main_window)

    def _save_portfolio(self):
        self.backend.save_portfolio()

    def _new_portfolio(self):
        NewPortfolioWindow(self.root, self.backend, self.main_window)

    def _exit_command(self):
        self.root.destroy()

    def _compare_assets(self):
        CompareWindow(self.root, self.backend)

    def _find_asset(self):
        FindAssetWindow(self.root, self.backend)




class MainWindowComponents:
    def __init__(self, window, backend: BackEnd):
        self.window = window
        self.backend = backend
        self.chart_dpi = 80
        self._define_buttons()
        self._define_asset_table()
        self.plot_history()
        self.plot_returns()
        self.plot_annualized_returns()
        self.plot_volatility()
        self.plot_correlation_matrix()
        self._place_components()
        self.display_portfolio_name()

    def _place_components(self):
        self.btn_change_position.grid(row = 1, column = 3, columnspan = 1)
        self.btn_recalculate_portfolio.grid(row = 1, column = 4, columnspan = 1)
        self.btn_analyze_portfolio.grid(row = 1, column = 5, columnspan = 1)
        self.asset_table.grid(row = 2, column = 1, columnspan = 5)

    def _define_buttons(self):
        self.btn_change_position = ctk.CTkButton(self.window, text="Change Position", command=self.change_position)
        self.btn_recalculate_portfolio = ctk.CTkButton(self.window, text="Recalculate Portfolio", command=self.recalculate_portfolio)
        self.btn_analyze_portfolio = ctk.CTkButton(self.window, text="Analyze Portfolio", command=self.analyze_portfolio)

    def display_portfolio_name(self):
        text = f"Portfolio name: {self.backend.portfolio.name}"
        self.lbl_portfolio_name = ctk.CTkLabel(self.window, text=text)
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
        figure = pyplot.Figure(figsize=(6,4), dpi=self.chart_dpi)
        ax = figure.add_subplot(111)
        self.main_plot_canvas = FigureCanvasTkAgg(figure, self.window)        
        ax.set_title('Value History')
        try:
            df = self.backend.portfolio.history[['Date', 'Value']]
        except AttributeError:
            pass
        else:
            df.plot(x='Date', y='Value', kind='line', legend=True, ax=ax)
        style_chart(figure)
        self.main_plot_canvas.get_tk_widget().grid(row = 2, column = 6, columnspan = 4)

    def plot_returns(self):
        figure = Figure(figsize=(6, 3), dpi=self.chart_dpi)
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
        style_chart(figure)
        self.returns_plot_canvas.get_tk_widget().grid(row = 3, column = 6, columnspan = 4)

    def plot_annualized_returns(self):
        figure = Figure(figsize=(6, 3), dpi=self.chart_dpi)
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
        style_chart(figure)
        self.annualized_returns_plot_canvas.get_tk_widget().grid(row = 3, column = 11, columnspan = 4)

    def plot_volatility(self):
        figure = Figure(figsize=(6, 3), dpi=self.chart_dpi)
        self.volatility_plot_canvas = FigureCanvasTkAgg(figure, self.window)
        axes = figure.add_subplot()
        try:
            periods = self.backend.portfolio.volatility.keys()
            returns = self.backend.portfolio.volatility.values()
        except AttributeError:
            pass
        else:
            bar = axes.bar(periods, returns)
            axes.set_title('Portfolio Volatility')
            axes.set_ylabel('%')
            axes.bar_label(bar)
        style_chart(figure)
        self.volatility_plot_canvas.get_tk_widget().grid(row = 3, column = 1, columnspan = 4)

    def plot_correlation_matrix(self):
        f = ctk.CTkFrame(self.window)
        f.grid(row = 2, column = 11, columnspan = 4)
        try:
            df = self.backend.portfolio.correlation_matrix
        except AttributeError:
            df = pd.DataFrame()
        self.table = pt = Table(f, dataframe=df,
                                showtoolbar=True, showstatusbar=True)
        pt.showindex = True
        config.apply_options(self._correlation_table_options(), pt)
        pt.show()

    def refresh_theme(self):
        config.apply_options(self._correlation_table_options(), self.table)
        self.table.redraw()

    def _correlation_table_options(self):
        dark_mode = ctk.get_appearance_mode() == "Dark"
        return {
            "colheadercolor": "#1f6aa5" if dark_mode else "green",
            "floatprecision": 3,
            "cellbackgr": "#2b2b2b" if dark_mode else "#F4F4F3",
            "textcolor": "#f2f2f2" if dark_mode else "black",
            "grid_color": "#555555" if dark_mode else "#ABB1AD",
            "rowselectedcolor": "#1f6aa5" if dark_mode else "#E4DED4",
        }

    def analyze_portfolio(self):
        AnalyzePortfolioWindow(self.window, self.backend)

    def change_position(self):
        self.change_position_window = ChangePositionWindow(self.window, self, self.backend)

    def recalculate_portfolio(self):
        self.backend.portfolio.calculate()
        self.display_portfolio_name()
        self.refresh_table()
        self.plot_history()
        self.plot_returns()
        self.plot_annualized_returns()
        self.plot_volatility()
        self.plot_correlation_matrix()

    def refresh_table(self):
        self.asset_table.delete(*self.asset_table.get_children())
        for asset in self.backend.portfolio.content.values():
            iid = len(self.asset_table.get_children())
            self.asset_table.insert(parent='',index='end',iid=iid,text='',
                                    values=(asset.ticker,
                                            asset.get_longname(),
                                            asset.quantity,
                                            round(asset.fast_info['previousClose'],2),
                                            round(asset.fast_info['previousClose']*asset.quantity)))
