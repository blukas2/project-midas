from types import SimpleNamespace
from unittest.mock import Mock

import pandas as pd
from matplotlib.figure import Figure

from ui.assets.find_asset import (
    FindAssetForCompareWindow,
    FindAssetForPositionWindow,
    FindAssetWindow,
)


class TestFindAssetWindow:
    def test_constructor_builds_controls_and_chart_placeholders(self, monkeypatch):
        popup = Mock()
        figure = Mock()
        monkeypatch.setattr("ui.assets.find_asset.ctk.CTkToplevel", Mock(return_value=popup))
        for name in ("CTkLabel", "CTkEntry", "CTkButton", "CTkScrollableFrame"):
            monkeypatch.setattr("ui.assets.find_asset.ctk." + name, Mock())
        monkeypatch.setattr("ui.assets.find_asset.tk.StringVar", Mock())
        monkeypatch.setattr("ui.assets.find_asset.ctk.CTkComboBox", Mock())
        monkeypatch.setattr("ui.assets.find_asset.Figure", Mock(return_value=figure))
        monkeypatch.setattr("ui.assets.find_asset.FigureCanvasTkAgg", Mock())

        window = FindAssetWindow(object(), Mock())

        assert window.window is popup
        assert window.show_in_eur is False
        assert window.search_results == []
        popup.title.assert_called_once_with("Find Asset")

    def test_position_picker_defaults_to_eur_and_exposes_select_buttons(self, monkeypatch):
        popup = Mock()
        monkeypatch.setattr("ui.assets.find_asset.ctk.CTkToplevel", Mock(return_value=popup))
        for name in ("CTkLabel", "CTkEntry", "CTkButton", "CTkScrollableFrame"):
            monkeypatch.setattr("ui.assets.find_asset.ctk." + name, Mock())
        monkeypatch.setattr("ui.assets.find_asset.tk.StringVar", Mock())
        monkeypatch.setattr("ui.assets.find_asset.ctk.CTkComboBox", Mock())
        monkeypatch.setattr("ui.assets.find_asset.Figure", Mock(return_value=Mock()))
        monkeypatch.setattr("ui.assets.find_asset.FigureCanvasTkAgg", Mock())
        callback = Mock()

        window = FindAssetForPositionWindow(object(), Mock(), callback)

        assert window.show_in_eur is True
        assert window.on_select_callback is callback
        window._currency_var.set.assert_called_with("EUR")

    def test_search_trims_query_and_populates_results(self):
        populate = Mock()
        window = FindAssetWindow.__new__(FindAssetWindow)
        window.entry_search = SimpleNamespace(get=lambda: " ABC ")
        window.backend = SimpleNamespace(
            asset_analyzer=SimpleNamespace(search=lambda query: [query])
        )
        window.search_results = []
        window._populate_results = populate

        window._on_search()

        assert window.search_results == ["ABC"]
        populate.assert_called_once_with()

    def test_populate_results_replaces_result_buttons(self, monkeypatch):
        window = FindAssetWindow.__new__(FindAssetWindow)
        window.listbox_results = Mock()
        window.search_results = ["ABC", "XYZ"]
        window._result_buttons = [Mock()]
        button_factory = Mock()
        monkeypatch.setattr("ui.assets.find_asset.ctk.CTkButton", button_factory)

        window._populate_results()

        assert len(window._result_buttons) == 2
        assert button_factory.call_count == 2
        window.listbox_results.winfo_children.assert_not_called()

    def test_empty_search_does_not_query_backend(self):
        search = Mock()
        window = FindAssetWindow.__new__(FindAssetWindow)
        window.entry_search = SimpleNamespace(get=lambda: "  ")
        window.backend = SimpleNamespace(asset_analyzer=SimpleNamespace(search=search))

        window._on_search()

        search.assert_not_called()

    def test_search_failure_shows_error(self, monkeypatch):
        window = FindAssetWindow.__new__(FindAssetWindow)
        window.window = Mock()
        window.entry_search = SimpleNamespace(get=lambda: "ABC")
        window.backend = SimpleNamespace(
            asset_analyzer=SimpleNamespace(search=Mock(side_effect=RuntimeError("offline")))
        )
        error = Mock()
        monkeypatch.setattr("ui.assets.find_asset.msgbox.showerror", error)

        window._on_search()

        error.assert_called_once()

    def test_selection_loads_ticker_and_refreshes_display(self):
        window = FindAssetWindow.__new__(FindAssetWindow)
        window.window = Mock()
        window._selected_result_index = 0
        window.search_results = [SimpleNamespace(ticker="ABC")]
        analyzer = SimpleNamespace(load_asset=Mock())
        window.backend = SimpleNamespace(asset_analyzer=analyzer)
        window._update_currency_dropdown = Mock()
        window._refresh_charts = Mock()

        window._on_select()

        analyzer.load_asset.assert_called_once_with("ABC")
        window._update_currency_dropdown.assert_called_once_with()
        window._refresh_charts.assert_called_once_with()

    def test_selection_without_row_is_ignored(self):
        analyzer = Mock()
        window = FindAssetWindow.__new__(FindAssetWindow)
        window._selected_result_index = None
        window.backend = SimpleNamespace(asset_analyzer=analyzer)

        window._on_select()

        analyzer.load_asset.assert_not_called()

    def test_selection_error_reports_ticker(self, monkeypatch):
        window = FindAssetWindow.__new__(FindAssetWindow)
        window.window = Mock()
        window._selected_result_index = 0
        window.search_results = [SimpleNamespace(ticker="BAD")]
        window.backend = SimpleNamespace(
            asset_analyzer=SimpleNamespace(load_asset=Mock(side_effect=ValueError("invalid")))
        )
        error = Mock()
        monkeypatch.setattr("ui.assets.find_asset.msgbox.showerror", error)

        window._on_select()

        assert "BAD" in error.call_args.kwargs["message"]

    def test_currency_handler_updates_state_and_charts(self):
        window = FindAssetWindow.__new__(FindAssetWindow)
        window._currency_var = SimpleNamespace(get=lambda: "EUR")
        window._refresh_charts = Mock()

        window._on_currency_change()

        assert window.show_in_eur is True
        window._refresh_charts.assert_called_once_with()

    def test_currency_dropdown_uses_asset_currency_and_current_selection(self):
        window = FindAssetWindow.__new__(FindAssetWindow)
        window.backend = SimpleNamespace(
            asset_analyzer=SimpleNamespace(native_currency="USD")
        )
        window.show_in_eur = True
        window.dropdown_currency = Mock()
        window._currency_var = Mock()

        window._update_currency_dropdown()

        window.dropdown_currency.configure.assert_called_once_with(values=["USD", "EUR"])
        window._currency_var.set.assert_called_once_with("EUR")

    def test_last_price_label_handles_available_and_missing_prices(self):
        window = FindAssetWindow.__new__(FindAssetWindow)
        window.backend = SimpleNamespace(
            asset_analyzer=SimpleNamespace(
                get_last_closing_price=lambda eur: 23.5,
                get_currency_label=lambda eur: "EUR",
            )
        )
        window.show_in_eur = True
        window.lbl_last_price = Mock()

        window._update_last_price_label()

        window.lbl_last_price.configure.assert_called_once_with(text="Last Close: 23.50 EUR")
        window.backend.asset_analyzer.get_last_closing_price = lambda eur: None
        window._update_last_price_label()
        window.lbl_last_price.configure.assert_called_with(text="")

    def test_position_picker_select_callback_and_close(self):
        window = FindAssetForPositionWindow.__new__(FindAssetForPositionWindow)
        window.selected_ticker = "ABC"
        window.on_select_callback = Mock()
        window.window = Mock()

        window._select_asset()

        window.on_select_callback.assert_called_once_with("ABC")
        window.window.destroy.assert_called_once_with()

    def test_grouped_returns_draw_asset_and_portfolio_bars(self):
        window = FindAssetForPositionWindow.__new__(FindAssetForPositionWindow)
        window.backend = SimpleNamespace(
            portfolio=SimpleNamespace(annualized_returns={"1y": 2, "5y": 5})
        )
        axes = Mock()
        axes.bar.side_effect = [object(), object()]

        window._plot_grouped_annualized_returns(axes, {"1y": 1, "3y": 3})

        assert axes.bar.call_count == 2
        axes.set_xticklabels.assert_called_once_with(["1y", "3y"])

    def test_refresh_charts_updates_price_and_annualized_returns(self, monkeypatch):
        history = SimpleNamespace(plot=Mock())
        analyzer = SimpleNamespace(
            get_last_closing_price=lambda eur: 12,
            get_currency_label=lambda eur: "USD",
            get_price_history=lambda eur: history,
            get_annualized_returns=lambda eur: {},
        )
        window = FindAssetWindow.__new__(FindAssetWindow)
        window.window = Mock()
        window.backend = SimpleNamespace(asset_analyzer=analyzer)
        window.show_in_eur = False
        window.lbl_last_price = Mock()
        window.price_figure = Mock()
        window.returns_figure = Mock()
        window.price_canvas = Mock()
        window.returns_canvas = Mock()
        window.price_figure.add_subplot.return_value = Mock()
        window.returns_figure.add_subplot.return_value = Mock()

        monkeypatch.setattr("ui.assets.find_asset.style_chart", Mock())
        window._refresh_charts()

        history.plot.assert_called_once()
        window.price_canvas.draw.assert_called_once()
        window.returns_canvas.draw.assert_called_once()
        window.lbl_last_price.configure.assert_called_once_with(text="Last Close: 12.00 USD")

    def test_position_picker_plots_eur_asset_against_portfolio(self, monkeypatch):
        dates = pd.to_datetime(["2024-01-01", "2024-01-02"])
        analyzer = SimpleNamespace(
            get_currency_label=lambda eur: "EUR",
            get_indexed_price_history=lambda in_eur: pd.DataFrame(
                {"Date": dates, "Asset": [100, 110]}
            ),
            get_portfolio_indexed_history=lambda portfolio: pd.DataFrame(
                {"Date": dates, "Portfolio": [100, 105]}
            ),
            get_annualized_returns=lambda in_eur: {"1y": 5},
        )
        window = FindAssetForPositionWindow.__new__(FindAssetForPositionWindow)
        window.backend = SimpleNamespace(
            asset_analyzer=analyzer,
            portfolio=SimpleNamespace(annualized_returns={"1y": 3}),
        )
        window.show_in_eur = True
        window.price_figure, window.returns_figure = Figure(), Figure()
        window.price_canvas, window.returns_canvas = Mock(), Mock()

        window._plot_price_history()
        window._plot_annualized_returns()

        window.price_canvas.draw.assert_called_once()
        window.returns_canvas.draw.assert_called_once()

    def test_picker_cancel_closes_without_selecting(self):
        window = FindAssetForCompareWindow.__new__(FindAssetForCompareWindow)
        window.on_select_callback = Mock()
        window.selected_ticker = None
        window.window = Mock()

        window._cancel()
        window.window.destroy.assert_called_once()
        window.window.destroy.reset_mock()
        window._select_asset()

        window.on_select_callback.assert_not_called()
        window.window.destroy.assert_called_once()
