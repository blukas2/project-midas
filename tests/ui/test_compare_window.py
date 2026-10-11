from types import SimpleNamespace
from unittest.mock import Mock

import pandas as pd

from ui.charts.figure_factory import FigureFactory
from ui.compare.compare import CompareWindow


class TestCompareWindow:
    def test_constructor_configures_controls_and_dashboard(self, monkeypatch):
        popup = Mock()
        monkeypatch.setattr("ui.compare.compare.ctk.CTkToplevel", Mock(return_value=popup))
        for name in ("CTkLabel", "CTkEntry", "CTkButton", "CTkComboBox"):
            monkeypatch.setattr("ui.compare.compare.ctk." + name, Mock())
        monkeypatch.setattr("ui.compare.compare.tk.StringVar", Mock())
        dashboard = Mock()
        monkeypatch.setattr("ui.compare.compare.PlotlyDashboard", Mock(return_value=dashboard))

        window = CompareWindow(object(), Mock())

        assert window._show_in_eur is True
        assert window._comparison_done is False
        assert window.dashboard is dashboard
        popup.title.assert_called_once_with("Compare assets")

    def test_compare_sets_state_and_displays_results(self):
        window = CompareWindow.__new__(CompareWindow)
        window._run_comparison = Mock()
        window._display_charts = Mock()
        window._currency_var = Mock()
        window._comparison_done = False
        window._show_in_eur = False

        window.compare()

        assert window._comparison_done is True
        assert window._show_in_eur is True
        window._currency_var.set.assert_called_once_with("EUR")
        window._display_charts.assert_called_once_with()

    def test_compare_handles_missing_asset(self, monkeypatch):
        window = CompareWindow.__new__(CompareWindow)
        window.window = Mock()
        window._comparison_done = False
        window._run_comparison = Mock(side_effect=AttributeError())
        error = Mock()
        monkeypatch.setattr("ui.compare.compare.msgbox.showerror", error)

        window.compare()

        error.assert_called_once()
        assert window._comparison_done is False

    def test_currency_change_waits_until_a_comparison_exists(self):
        window = CompareWindow.__new__(CompareWindow)
        window._comparison_done = False
        window.backend = SimpleNamespace(comparer=Mock())

        window._on_currency_change()

        window.backend.comparer.recalculate.assert_not_called()

    def test_currency_change_recalculates_and_renders(self):
        window = CompareWindow.__new__(CompareWindow)
        window._comparison_done = True
        window._currency_var = SimpleNamespace(get=lambda: "Local")
        window.backend = SimpleNamespace(comparer=SimpleNamespace(recalculate=Mock()))
        window._display_charts = Mock()

        window._on_currency_change()

        assert window._show_in_eur is False
        window.backend.comparer.recalculate.assert_called_once_with(False)
        window._display_charts.assert_called_once_with()

    def test_run_comparison_requires_two_tickers(self):
        window = CompareWindow.__new__(CompareWindow)
        window._use_portfolio_for_asset1 = False
        window._use_portfolio_for_asset2 = False
        window.entry_asset1_ticker = SimpleNamespace(get=lambda: "AAA")
        window.entry_asset2_ticker = SimpleNamespace(get=lambda: "BBB")
        comparer = SimpleNamespace(compare=Mock())
        window.backend = SimpleNamespace(portfolio=object(), comparer=comparer)

        window._run_comparison()

        comparer.compare.assert_called_once_with("AAA", "BBB")

    def test_run_comparison_can_use_portfolio_for_asset1(self):
        window = CompareWindow.__new__(CompareWindow)
        window._use_portfolio_for_asset1 = True
        window._use_portfolio_for_asset2 = False
        window.entry_asset2_ticker = SimpleNamespace(get=lambda: "BBB")
        portfolio = object()
        comparer = SimpleNamespace(compare_with_portfolio=Mock())
        window.backend = SimpleNamespace(portfolio=portfolio, comparer=comparer)

        window._run_comparison()

        comparer.compare_with_portfolio.assert_called_once_with(portfolio, "BBB", 1)

    def test_empty_portfolio_is_rejected(self, monkeypatch):
        window = CompareWindow.__new__(CompareWindow)
        window.window = Mock()
        window.backend = SimpleNamespace(portfolio=SimpleNamespace(content={}))
        error = Mock()
        monkeypatch.setattr("ui.compare.compare.msgbox.showerror", error)

        assert window._is_portfolio_loaded() is False
        error.assert_called_once()

    def test_use_portfolio_sets_flag_and_entry(self):
        window = CompareWindow.__new__(CompareWindow)
        window._is_portfolio_loaded = Mock(return_value=True)
        window._set_entry_to_portfolio_name = Mock()
        window.entry_asset1_ticker = object()

        window._use_portfolio_as_asset1()

        assert window._use_portfolio_for_asset1 is True
        window._set_entry_to_portfolio_name.assert_called_once_with(window.entry_asset1_ticker)

    def test_ticker_read_reports_value_error(self, monkeypatch):
        window = CompareWindow.__new__(CompareWindow)
        window.window = Mock()
        error = Mock()
        monkeypatch.setattr("ui.compare.compare.msgbox.showerror", error)

        result = window._read_ticker(SimpleNamespace(get=Mock(side_effect=ValueError)), "Asset 1")

        assert result is None
        error.assert_called_once()

    def test_portfolio_name_populates_entry_and_disables_it(self):
        window = CompareWindow.__new__(CompareWindow)
        window.backend = SimpleNamespace(portfolio=SimpleNamespace(name="Fund", content={"ABC": object()}))
        entry = Mock()

        window._set_entry_to_portfolio_name(entry)

        entry.insert.assert_called_once_with(0, "Fund")
        entry.configure.assert_called_once_with(state="disabled")

    def test_comparison_renders_history_and_grouped_metrics(self, monkeypatch):
        dates = pd.to_datetime(["2024-01-01", "2024-01-02"])
        comparer = SimpleNamespace(
            asset1_name="Alpha",
            asset2_name="Beta",
            compare_table=pd.DataFrame({
                "Date": dates,
                "asset1_price_index": [100, 110],
                "asset2_price_index": [100, 105],
            }),
            asset1_annualized_returns={"1y": 5},
            asset2_annualized_returns={"1y": 3},
            asset1_volatility={"1y": 10},
            asset2_volatility={"1y": 8},
        )
        window = CompareWindow.__new__(CompareWindow)
        window.backend = SimpleNamespace(comparer=comparer)
        window.chart_factory = FigureFactory()
        window.dashboard = Mock()
        window._currency_var = SimpleNamespace(get=lambda: "EUR")
        monkeypatch.setattr("ui.compare.compare.ctk.get_appearance_mode", lambda: "Light")

        window._display_charts()

        figures = window.dashboard.render.call_args.args[0]
        assert list(figures["comparison-history"].data[0].y) == [100, 110]
        assert list(figures["comparison-returns"].data[0].y) == [5.0]
        assert list(figures["comparison-volatility"].data[1].y) == [8.0]
        assert window.dashboard.render.call_args.kwargs["subtitle"] == "Comparison in EUR"
