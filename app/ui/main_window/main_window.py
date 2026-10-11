from __future__ import annotations

import tkinter as tk
from tkinter import Menu
from typing import TYPE_CHECKING

import customtkinter as ctk
import pandas as pd

from ui.assets.find_asset import FindAssetWindow
from ui.charts.figure_factory import FigureFactory
from ui.charts.page_builder import ChartCardSpec
from ui.charts.plotly_dashboard import PlotlyDashboard
from ui.compare.compare import CompareWindow
from ui.main_window.analyze_portfolio import AnalyzePortfolioWindow
from ui.main_window.popups import ChangePositionWindow, NewPortfolioWindow, OpenPortfolioWindow
from ui.theme import toggle_appearance_mode

if TYPE_CHECKING:
    from backend.backend import BackEnd


class DropdownMenu:
    def __init__(self, root: tk.Tk, backend: BackEnd, main_window: MainWindowComponents):
        self.root = root
        self.main_window = main_window
        self.backend = backend
        self.menu_frame = ctk.CTkFrame(root, corner_radius=0)
        self.menu_frame.grid(row=0, column=0, columnspan=8, sticky="ew")
        self._define_portfolio_menu()
        self._define_assets_menu()
        self._define_analysis_menu()
        self._define_theme_button()

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

    def _define_theme_button(self):
        self.theme_button = ctk.CTkButton(
            self.menu_frame,
            text=f"Theme: {ctk.get_appearance_mode()}",
            command=self._toggle_theme,
        )
        self.theme_button.pack(side="right", padx=8, pady=6)

    def _create_menu(self, title: str):
        menu = Menu(self.root, tearoff=False)
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
        self.chart_factory = FigureFactory()
        self._define_buttons()
        self._define_dashboard()
        self._place_components()
        self.refresh_table()

    def _define_buttons(self):
        self.toolbar_frame = ctk.CTkFrame(self.window, corner_radius=0, fg_color="transparent")
        self.btn_change_position = ctk.CTkButton(
            self.toolbar_frame, text="Change Position", command=self.change_position
        )
        self.btn_recalculate_portfolio = ctk.CTkButton(
            self.toolbar_frame, text="Recalculate Portfolio", command=self.recalculate_portfolio
        )
        self.btn_analyze_portfolio = ctk.CTkButton(
            self.toolbar_frame, text="Analyze Portfolio", command=self.analyze_portfolio
        )

    def _define_dashboard(self):
        cards = [
            ChartCardSpec("portfolio-history", "Portfolio value history", wide=True),
            ChartCardSpec("allocation", "Portfolio allocation"),
            ChartCardSpec("portfolio-returns", "Portfolio returns"),
            ChartCardSpec("annualized-returns", "Annualized returns"),
            ChartCardSpec("portfolio-volatility", "Volatility"),
            ChartCardSpec("correlation", "Asset correlation", wide=True),
        ]
        self.dashboard = PlotlyDashboard(
            self.window, "Portfolio dashboard", cards, include_metrics=True, include_holdings=True
        )

    def _place_components(self):
        self.toolbar_frame.grid(row=1, column=0, columnspan=8, sticky="ew", padx=8, pady=6)
        self.btn_change_position.pack(side="left", padx=4)
        self.btn_recalculate_portfolio.pack(side="left", padx=4)
        self.btn_analyze_portfolio.pack(side="left", padx=4)
        self.display_portfolio_name()
        self.dashboard.grid(row=2, column=0, columnspan=8, sticky="nsew", padx=10, pady=(0, 10))
        self.window.rowconfigure(2, weight=1)
        for column in range(8):
            self.window.columnconfigure(column, weight=1)

    def display_portfolio_name(self):
        text = f"Portfolio: {self.backend.portfolio.name or 'Untitled'}"
        if hasattr(self, "lbl_portfolio_name"):
            self.lbl_portfolio_name.configure(text=text)
        else:
            self.lbl_portfolio_name = ctk.CTkLabel(self.toolbar_frame, text=text)
        self.lbl_portfolio_name.pack(side="left", padx=(12, 8))

    def refresh_theme(self):
        self.dashboard.set_theme(ctk.get_appearance_mode())

    def analyze_portfolio(self):
        AnalyzePortfolioWindow(self.window, self.backend)

    def change_position(self):
        self.change_position_window = ChangePositionWindow(self.window, self, self.backend)

    def recalculate_portfolio(self):
        self.backend.portfolio.calculate()
        self.display_portfolio_name()
        self.refresh_table()

    def refresh_table(self):
        figures = self._build_figures()
        metrics = self._build_metrics()
        headers = ("Ticker", "Name", "Quantity", "Unit price", "Value")
        self.dashboard.render(
            figures, metrics, headers, self._holdings_rows(), self.backend.portfolio.name or ""
        )

    def _build_figures(self):
        portfolio = self.backend.portfolio
        mode = ctk.get_appearance_mode()
        return {
            "portfolio-history": self._history_figure(portfolio, mode),
            "allocation": self.chart_factory.donut_chart(self._allocation_values(), mode),
            "portfolio-returns": self.chart_factory.bar_chart(getattr(portfolio, "returns", {}), mode),
            "annualized-returns": self.chart_factory.bar_chart(
                getattr(portfolio, "annualized_returns", {}), mode
            ),
            "portfolio-volatility": self.chart_factory.bar_chart(
                getattr(portfolio, "volatility", {}), mode, "Volatility"
            ),
            "correlation": self.chart_factory.heatmap(
                getattr(portfolio, "correlation_matrix", pd.DataFrame()), mode
            ),
        }

    def _history_figure(self, portfolio, mode):
        history = getattr(portfolio, "history", pd.DataFrame())
        series = []
        if not history.empty and {"Date", "Value"}.issubset(history.columns):
            series.append(("Portfolio value", history["Date"].tolist(), history["Value"].tolist()))
        return self.chart_factory.line_chart(series, mode, "Value (EUR)")

    def _allocation_values(self):
        values = {}
        for ticker, asset in self.backend.portfolio.content.items():
            if not asset.price_history.empty:
                values[ticker] = float(asset.price_history["Price"].iloc[-1]) * asset.quantity
        return values

    def _build_metrics(self):
        portfolio = self.backend.portfolio
        history = getattr(portfolio, "history", pd.DataFrame())
        value = f"{history['Value'].iloc[-1]:,.0f} EUR" if not history.empty else "N/A"
        returns = getattr(portfolio, "returns", {})
        annualized = getattr(portfolio, "annualized_returns", {})
        volatility = getattr(portfolio, "volatility", {})
        return [
            ("Current value", value),
            ("1-year return", self._format_metric(returns.get("1y"))),
            ("1-year annualized", self._format_metric(annualized.get("1y"))),
            ("1-year volatility", self._format_metric(volatility.get("1y"))),
            ("Positions", str(len(portfolio.content))),
        ]

    def _format_metric(self, value):
        return f"{value:.1f}%" if value is not None else "N/A"

    def _holdings_rows(self):
        rows = []
        for asset in self.backend.portfolio.content.values():
            rows.append(self._holdings_row(asset))
        return rows

    def _holdings_row(self, asset):
        price = float(asset.price_history["Price"].iloc[-1]) if not asset.price_history.empty else 0.0
        return (
            asset.ticker,
            asset.get_longname(),
            str(asset.quantity),
            f"{price:,.2f} EUR",
            f"{price * asset.quantity:,.2f} EUR",
        )
