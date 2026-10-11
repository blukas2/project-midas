from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock

import pandas as pd

from backend.comparer.comparer import Comparer


class TestComparer:
    def test_eur_copy_is_skipped_for_native_euro_asset(self, monkeypatch):
        comparer = Comparer()
        euro_asset = SimpleNamespace(fast_info={"currency": "EUR"})

        assert comparer._prepare_eur_copy(euro_asset) is None

    def test_compare_loads_both_assets_and_recalculates(self, monkeypatch):
        comparer = Comparer()
        assets = {
            "AAA": SimpleNamespace(get_longname=lambda: "Alpha", fast_info={"currency": "EUR"}),
            "BBB": SimpleNamespace(get_longname=lambda: "Beta", fast_info={"currency": "EUR"}),
        }
        monkeypatch.setattr("backend.comparer.comparer.Asset", lambda ticker, quantity: assets[ticker])
        comparer.recalculate = Mock()

        comparer.compare("AAA", "BBB")

        assert comparer.asset1_name == "Alpha"
        assert comparer.asset2_name == "Beta"
        comparer.recalculate.assert_called_once_with(in_eur=True)

    def test_compare_with_portfolio_sets_selected_slot(self, monkeypatch):
        comparer = Comparer()
        asset = SimpleNamespace(get_longname=lambda: "Alpha", fast_info={"currency": "EUR"})
        monkeypatch.setattr("backend.comparer.comparer.Asset", lambda ticker, quantity: asset)
        comparer.recalculate = Mock()
        portfolio = SimpleNamespace(
            name="Fund",
            history=pd.DataFrame({"Date": [date(2024, 1, 1)], "Value": [10]}),
        )

        comparer.compare_with_portfolio(portfolio, "AAA", 2)

        assert comparer.asset1 is asset
        assert comparer.asset2 is None
        assert comparer.asset2_name == "Fund"
        assert comparer._portfolio_position == 2
        comparer.recalculate.assert_called_once_with(in_eur=True)

    def test_build_compare_table_joins_on_common_dates(self):
        comparer = Comparer()
        first = pd.DataFrame({"Date": [date(2024, 1, 1), date(2024, 1, 2)], "Price": [10, 12]})
        second = pd.DataFrame({"Date": [date(2024, 1, 2), date(2024, 1, 3)], "Price": [20, 24]})

        comparer._build_compare_table(first, second)

        assert comparer.compare_table["asset1_price"].tolist() == [12]
        assert comparer.compare_table["asset2_price"].tolist() == [20]

    def test_recalculate_builds_indices_and_metrics(self, monkeypatch):
        comparer = Comparer()
        dates = pd.bdate_range("2020-01-01", periods=10).date
        first = SimpleNamespace(price_history=pd.DataFrame({"Date": dates, "Price": range(10, 20)}))
        second = SimpleNamespace(price_history=pd.DataFrame({"Date": dates, "Price": range(20, 30)}))
        comparer.asset1, comparer.asset2 = first, second
        comparer.asset1_eur = comparer.asset2_eur = None
        comparer.returns_calculator.calculate_annualized_returns = lambda *args: {"1y": 1}
        comparer.returns_calculator.calculate_volatility = lambda *args: {"1y": 2}

        comparer.recalculate(False)

        assert comparer.compare_table["asset1_price_index"].iloc[0] == 100
        assert comparer.compare_table["asset2_price_index"].iloc[0] == 100
        assert comparer.asset1_annualized_returns == {"1y": 1}
        assert comparer.asset2_volatility == {"1y": 2}

    def test_get_asset_history_selects_eur_copy_or_portfolio(self):
        comparer = Comparer()
        native = SimpleNamespace(price_history="native")
        euro = SimpleNamespace(price_history="euro")
        portfolio_history = "portfolio"
        comparer.asset1, comparer.asset1_eur = native, euro
        comparer.asset2 = None
        comparer.asset2_eur = None
        comparer._portfolio_position = 2
        comparer._portfolio_history = portfolio_history

        assert comparer._get_asset_history(1, True) == "euro"
        assert comparer._get_asset_history(1, False) == "native"
        assert comparer._get_asset_history(2, True) is portfolio_history
