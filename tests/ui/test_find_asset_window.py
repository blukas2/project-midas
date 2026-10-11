from types import SimpleNamespace
from unittest.mock import Mock

import pandas as pd

from ui.assets.find_asset import (
    FindAssetForCompareWindow,
    FindAssetForPositionWindow,
    FindAssetWindow,
)


class TestFindAssetWindow:
    def test_constructor_builds_controls_and_dashboard(self, monkeypatch):
        popup = Mock()
        monkeypatch.setattr("ui.assets.find_asset.ctk.CTkToplevel", Mock(return_value=popup))
        for name in ("CTkLabel", "CTkEntry", "CTkButton", "CTkScrollableFrame"):
            monkeypatch.setattr("ui.assets.find_asset.ctk." + name, Mock())
        monkeypatch.setattr("ui.assets.find_asset.tk.StringVar", Mock())
        monkeypatch.setattr("ui.assets.find_asset.ctk.CTkComboBox", Mock())
        dashboard = Mock()
        monkeypatch.setattr("ui.assets.find_asset.PlotlyDashboard", Mock(return_value=dashboard))

        window = FindAssetWindow(object(), Mock())

        assert window.window is popup
        assert window.show_in_eur is False
        assert window.search_results == []
        assert window.chart_dashboard is dashboard
        popup.title.assert_called_once_with("Find Asset")

    def test_position_picker_defaults_to_eur_and_exposes_select_buttons(self, monkeypatch):
        popup = Mock()
        monkeypatch.setattr("ui.assets.find_asset.ctk.CTkToplevel", Mock(return_value=popup))
        for name in ("CTkLabel", "CTkEntry", "CTkButton", "CTkScrollableFrame"):
            monkeypatch.setattr("ui.assets.find_asset.ctk." + name, Mock())
        monkeypatch.setattr("ui.assets.find_asset.tk.StringVar", Mock())
        monkeypatch.setattr("ui.assets.find_asset.ctk.CTkComboBox", Mock())
        monkeypatch.setattr("ui.assets.find_asset.PlotlyDashboard", Mock(return_value=Mock()))
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

    def test_position_returns_group_asset_and_portfolio_values(self):
        window = FindAssetForPositionWindow.__new__(FindAssetForPositionWindow)
        window.backend = SimpleNamespace(
            portfolio=SimpleNamespace(annualized_returns={"1y": 2, "5y": 5})
        )
        window.chart_factory = Mock()
        window.show_in_eur = True

        window._position_returns_figure({"1y": 1, "3y": 3})

        window.chart_factory.grouped_bar_chart.assert_called_once_with(
            [("Asset", {"1y": 1, "3y": 3}), ("Portfolio", {"1y": 2, "5y": 5})],
            "Light",
        )

    def test_refresh_charts_updates_dashboard_and_last_price(self):
        analyzer = SimpleNamespace(
            get_last_closing_price=lambda eur: 12,
            get_currency_label=lambda eur: "USD",
        )
        window = FindAssetWindow.__new__(FindAssetWindow)
        window.backend = SimpleNamespace(asset_analyzer=analyzer)
        window.show_in_eur = False
        window.lbl_last_price = Mock()
        window.chart_dashboard = Mock()
        window._build_chart_figures = Mock(return_value={"history": object()})

        window._refresh_charts()

        window.chart_dashboard.render.assert_called_once_with(
            window._build_chart_figures.return_value
        )
        window.lbl_last_price.configure.assert_called_once_with(text="Last Close: 12.00 USD")

    def test_position_picker_builds_eur_asset_and_portfolio_charts(self):
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
            portfolio=SimpleNamespace(history=pd.DataFrame(), annualized_returns={"1y": 3}),
        )
        window.chart_factory = Mock()
        window.show_in_eur = True

        window._build_chart_figures()

        series = window.chart_factory.line_chart.call_args.args[0]
        assert [item[0] for item in series] == ["Asset", "Portfolio"]
        window.chart_factory.grouped_bar_chart.assert_called_once()

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
