from datetime import date, timedelta
from types import SimpleNamespace

import pandas as pd

from backend.asset_analyzer import AssetAnalyzer


class TestAssetAnalyzer:
    def test_search_delegates_query(self, monkeypatch):
        analyzer = AssetAnalyzer()
        result = object()
        monkeypatch.setattr(analyzer.asset_finder, "find_assets", lambda query: [result])

        assert analyzer.search("query") == [result]

    def test_price_history_filters_to_recent_five_years(self, monkeypatch):
        analyzer = AssetAnalyzer()
        recent = date.today()
        history = pd.DataFrame(
            {"Date": [recent - timedelta(days=6 * 365), recent], "Price": [10, 20]}
        )
        monkeypatch.setattr(analyzer, "_get_history_table", lambda in_eur: history)

        actual = analyzer.get_price_history(False)

        assert actual["Price"].tolist() == [20]
        assert list(actual.columns) == ["Date", "Price"]

    def test_indexed_history_starts_at_100(self, monkeypatch):
        analyzer = AssetAnalyzer()
        history = pd.DataFrame(
            {"Date": [date(2024, 1, 1), date(2024, 1, 2)], "Price": [5, 10]}
        )
        monkeypatch.setattr(analyzer, "get_price_history", lambda in_eur: history)

        assert analyzer.get_indexed_price_history(False)["Asset"].tolist() == [100, 200]

    def test_portfolio_index_is_aligned_and_returns_empty_frame(self, monkeypatch):
        analyzer = AssetAnalyzer()
        asset_history = pd.DataFrame({"Date": [date(2024, 1, 1)], "Price": [5]})
        portfolio = SimpleNamespace(
            history=pd.DataFrame(
                {"Date": [date(2024, 1, 1), date(2024, 1, 2)], "Value": [5, 10]}
            )
        )
        monkeypatch.setattr(analyzer, "get_price_history", lambda in_eur: asset_history)

        assert analyzer.get_portfolio_indexed_history(portfolio)["Portfolio"].tolist() == [100, 200]
        portfolio.history = portfolio.history.iloc[:0]
        assert list(analyzer.get_portfolio_indexed_history(portfolio).columns) == ["Date", "Portfolio"]

    def test_last_price_and_currency_label(self):
        analyzer = AssetAnalyzer()
        analyzer.asset = SimpleNamespace(price_history=pd.DataFrame({"Price": [42.5]}))
        analyzer.native_currency = "USD"

        assert analyzer.get_last_closing_price(False) == 42.5
        assert analyzer.get_currency_label(True) == "EUR"
        assert analyzer.get_currency_label(False) == "USD"

    def test_no_loaded_asset_has_no_last_price(self):
        assert AssetAnalyzer().get_last_closing_price(True) is None

    def test_get_annualized_returns_delegates_with_price_data(self, monkeypatch):
        analyzer = AssetAnalyzer()
        history = pd.DataFrame({"Date": [date(2024, 1, 1)], "Price": [10]})
        expected = {"1y": 1.5}
        monkeypatch.setattr(analyzer, "get_price_history", lambda eur: history)
        monkeypatch.setattr(
            analyzer.returns_calculator,
            "calculate_annualized_returns",
            lambda received, column: expected if received is history and column == "Price" else None,
        )

        assert analyzer.get_annualized_returns(False) == expected

    def test_eur_conversion_is_only_created_for_non_euro_assets(self, monkeypatch):
        analyzer = AssetAnalyzer()
        analyzer.asset = SimpleNamespace(ticker="ABC")
        analyzer.native_currency = "EUR"
        analyzer._prepare_eur_conversion()
        assert analyzer.asset_eur is None

        analyzer.native_currency = "USD"
        cross_fx = object()
        eur_asset = SimpleNamespace(convert_fx=lambda fx: setattr(eur_asset, "fx", fx))
        monkeypatch.setattr("backend.asset_analyzer.CrossFx", lambda **kwargs: cross_fx)
        monkeypatch.setattr("backend.asset_analyzer.Asset", lambda ticker, quantity: eur_asset)

        analyzer._prepare_eur_conversion()

        assert analyzer.asset_eur is eur_asset
        assert eur_asset.fx is cross_fx

    def test_history_selector_prefers_converted_copy_when_requested(self):
        analyzer = AssetAnalyzer()
        analyzer.asset = SimpleNamespace(price_history="native")
        analyzer.asset_eur = SimpleNamespace(price_history="converted")

        assert analyzer._get_history_table(True) == "converted"
        assert analyzer._get_history_table(False) == "native"
