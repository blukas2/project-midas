from __future__ import annotations

import tkinter as tk
import customtkinter as ctk

from ui.charts.figure_factory import FigureFactory
from ui.charts.page_builder import ChartCardSpec
from ui.charts.plotly_dashboard import PlotlyDashboard
from ui.dialogs import ThemedMessageBox as msgbox

from typing import Callable, TYPE_CHECKING
if TYPE_CHECKING:
    from backend.backend import BackEnd


class FindAssetWindow:
    """Window for searching assets, viewing price history and annualized returns."""

    def __init__(self, master, backend: BackEnd):
        self.backend = backend
        self.window = ctk.CTkToplevel(master)
        self.window.title("Find Asset")
        self.window.geometry("1000x900")
        self.chart_factory = FigureFactory()
        self.show_in_eur = False
        self.search_results = []
        self._selected_result_index: int | None = None
        self._result_buttons = []
        self._define_search_section()
        self._define_results_section()
        self._define_currency_dropdown()
        self._define_chart_dashboard()
        self._place_components()

    def _define_search_section(self):
        self.lbl_search = ctk.CTkLabel(self.window, text="Search:")
        self.entry_search = ctk.CTkEntry(self.window, width=320)
        self.btn_search = ctk.CTkButton(self.window, text="Search", command=self._on_search)

    def _define_results_section(self):
        self.lbl_results = ctk.CTkLabel(self.window, text="Results:")
        self.listbox_results = ctk.CTkScrollableFrame(self.window, width=520, height=180)

    def _define_currency_dropdown(self):
        self._currency_var = tk.StringVar(value="Local")
        self.dropdown_currency = ctk.CTkComboBox(
            self.window,
            variable=self._currency_var,
            values=["Local", "EUR"],
            state="readonly",
            width=160,
            command=self._on_currency_change,
        )
        self.lbl_last_price = ctk.CTkLabel(self.window, text="", anchor="w")

    def _define_chart_dashboard(self):
        cards = [
            ChartCardSpec("asset-history", "Price history", wide=True),
            ChartCardSpec("asset-returns", "Annualized returns"),
        ]
        self.chart_dashboard = PlotlyDashboard(self.window, "Asset details", cards, height=620)

    def _place_components(self):
        self.lbl_search.grid(row=1, column=1)
        self.entry_search.grid(row=1, column=2, columnspan=2)
        self.btn_search.grid(row=1, column=4)
        self.lbl_results.grid(row=2, column=1, sticky='nw')
        self.listbox_results.grid(row=2, column=2, columnspan=3, pady=5, sticky="ew")
        self.dropdown_currency.grid(row=3, column=1, columnspan=2, pady=5)
        self.lbl_last_price.grid(row=3, column=3, columnspan=2, pady=5, sticky='w')
        self.chart_dashboard.grid(row=4, column=1, columnspan=5, sticky="nsew", padx=8, pady=8)
        self.window.rowconfigure(4, weight=1)
        for column in range(1, 6):
            self.window.columnconfigure(column, weight=1)

    def _on_search(self):
        query = self.entry_search.get().strip()
        if not query:
            return
        try:
            self.search_results = self.backend.asset_analyzer.search(query)
        except Exception:
            msgbox.showerror(title="Error", message="Search failed. Please try again.", parent=self.window)
            return
        self._populate_results()

    def _populate_results(self):
        for button in self._result_buttons:
            button.destroy()
        self._result_buttons.clear()
        self._selected_result_index = None
        for index, result in enumerate(self.search_results):
            button = ctk.CTkButton(
                self.listbox_results,
                text=str(result),
                anchor="w",
                command=lambda selected=index: self._on_select(index=selected),
            )
            button.pack(fill="x", padx=4, pady=2)
            self._result_buttons.append(button)

    def _on_select(self, event=None, index: int | None = None):
        if index is not None:
            self._selected_result_index = index
        if self._selected_result_index is None:
            return
        selected = self.search_results[self._selected_result_index]
        try:
            self.backend.asset_analyzer.load_asset(selected.ticker)
        except Exception:
            msgbox.showerror(
                title="Error",
                message=f"Could not load '{selected.ticker}'.",
                parent=self.window,
            )
            return
        self._update_currency_dropdown()
        self._refresh_charts()

    def _on_currency_change(self, event=None):
        self.show_in_eur = self._currency_var.get() == "EUR"
        self._refresh_charts()

    def _update_currency_dropdown(self):
        native = self.backend.asset_analyzer.native_currency
        current = "EUR" if self.show_in_eur else native
        self.dropdown_currency.configure(values=[native, "EUR"])
        self._currency_var.set(current)

    def _refresh_charts(self):
        self._update_last_price_label()
        self.chart_dashboard.render(self._build_chart_figures())

    def _update_last_price_label(self):
        analyzer = self.backend.asset_analyzer
        price = analyzer.get_last_closing_price(self.show_in_eur)
        if price is None:
            self.lbl_last_price.configure(text="")
            return
        currency = analyzer.get_currency_label(self.show_in_eur)
        self.lbl_last_price.configure(text=f"Last Close: {price:.2f} {currency}")

    def _build_chart_figures(self):
        analyzer = self.backend.asset_analyzer
        currency = analyzer.get_currency_label(self.show_in_eur)
        history = analyzer.get_price_history(self.show_in_eur)
        series = [("Asset", history["Date"].tolist(), history["Price"].tolist())]
        returns = analyzer.get_annualized_returns(self.show_in_eur)
        return self._chart_figures(series, currency, returns)

    def _chart_figures(self, series, currency, returns):
        mode = ctk.get_appearance_mode()
        history = self.chart_factory.line_chart(series, mode, currency)
        annualized = self.chart_factory.bar_chart(returns, mode)
        return {"asset-history": history, "asset-returns": annualized}

    def _native_history_series(self):
        history = self.backend.asset_analyzer.get_price_history(self.show_in_eur)
        return [("Asset", history["Date"].tolist(), history["Price"].tolist())]


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
        self.btn_select = ctk.CTkButton(self.window, text="Select Asset", command=self._select_asset)
        self.btn_cancel = ctk.CTkButton(self.window, text="Cancel", command=self._cancel)
        self.btn_select.grid(row=3, column=6, pady=5)
        self.btn_cancel.grid(row=3, column=7, pady=5)

    def _on_select(self, event=None, index: int | None = None):
        if index is not None:
            self._selected_result_index = index
        if self._selected_result_index is None:
            return
        self.selected_ticker = self.search_results[self._selected_result_index].ticker
        super()._on_select(event, self._selected_result_index)

    def _build_chart_figures(self):
        analyzer = self.backend.asset_analyzer
        currency = analyzer.get_currency_label(self.show_in_eur)
        history = self._position_history_series()
        asset_returns = analyzer.get_annualized_returns(self.show_in_eur)
        returns = self._position_returns_figure(asset_returns)
        axis_title = "Index (100 = start)" if self.show_in_eur else currency
        return {
            "asset-history": self.chart_factory.line_chart(history, ctk.get_appearance_mode(), axis_title),
            "asset-returns": returns,
        }

    def _position_history_series(self):
        analyzer = self.backend.asset_analyzer
        if not self.show_in_eur:
            return self._native_history_series()
        asset_history = analyzer.get_indexed_price_history(in_eur=True)
        series = [("Asset", asset_history["Date"].tolist(), asset_history["Asset"].tolist())]
        if hasattr(self.backend.portfolio, "history"):
            series.extend(self._portfolio_history_series(analyzer, self.backend.portfolio))
        return series

    def _portfolio_history_series(self, analyzer, portfolio):
        history = analyzer.get_portfolio_indexed_history(portfolio)
        if history.empty:
            return []
        return [("Portfolio", history["Date"].tolist(), history["Portfolio"].tolist())]

    def _position_returns_figure(self, asset_returns):
        mode = ctk.get_appearance_mode()
        if not self.show_in_eur:
            return self.chart_factory.bar_chart(asset_returns, mode)
        portfolio_returns = getattr(self.backend.portfolio, "annualized_returns", {})
        return self.chart_factory.grouped_bar_chart(
            [("Asset", asset_returns), ("Portfolio", portfolio_returns)], mode
        )

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
        self.btn_select = ctk.CTkButton(self.window, text="Select Asset", command=self._select_asset)
        self.btn_cancel = ctk.CTkButton(self.window, text="Cancel", command=self._cancel)
        self.btn_select.grid(row=3, column=6, pady=5)
        self.btn_cancel.grid(row=3, column=7, pady=5)

    def _on_select(self, event=None, index: int | None = None):
        if index is None and self._selected_result_index is None:
            return
        selected_index = index if index is not None else self._selected_result_index
        self.selected_ticker = self.search_results[selected_index].ticker
        super()._on_select(event, selected_index)

    def _select_asset(self):
        if self.selected_ticker:
            self.on_select_callback(self.selected_ticker)
        self.window.destroy()

    def _cancel(self):
        self.window.destroy()
