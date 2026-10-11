from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest

from backend.portfolio.portfolio import Portfolio


class TestPortfolioInitialization:
    def test_constructor_loads_names_and_initializes_content(self, tmp_path, monkeypatch):
        names_file = tmp_path / "names.json"
        names_file.write_text('{"ABC": "Alpha"}')
        monkeypatch.setattr("backend.portfolio.portfolio.ASSET_NAMES_FILE", str(names_file))
        monkeypatch.setattr(
            "backend.portfolio.portfolio.ReferenceAssets",
            lambda: SimpleNamespace(repository={}),
        )

        portfolio = Portfolio("Fund")

        assert portfolio.name == "Fund"
        assert portfolio.asset_names_dict == {"ABC": "Alpha"}
        assert portfolio.content == {}

    def test_add_asset_updates_existing_quantity_and_rejects_negative(self, portfolio_stub, monkeypatch):
        holding = FakeAsset(2, "ABC")
        portfolio_stub.content["ABC"] = holding
        asset_factory = Mock()
        monkeypatch.setattr("backend.portfolio.portfolio.Asset", asset_factory)

        portfolio_stub.add_asset("ABC", 3)

        assert holding.quantity == 5
        asset_factory.assert_not_called()
        with pytest.raises(ValueError, match="Quantity cannot be added"):
            portfolio_stub.add_asset("ABC", -1)

    def test_add_asset_resolves_name_and_reference_for_new_holding(self, portfolio_stub, monkeypatch):
        reference = object()
        portfolio_stub.reference_assets = SimpleNamespace(
            retrieve_long_name=lambda ticker: "Alpha",
            get_reference_asset=lambda ticker: reference,
        )
        asset = object()
        factory = Mock(return_value=asset)
        monkeypatch.setattr("backend.portfolio.portfolio.Asset", factory)

        portfolio_stub.add_asset("ABC", 4)

        factory.assert_called_once_with("ABC", 4, long_name="Alpha", reference_asset=reference)
        assert portfolio_stub.content["ABC"] is asset


class TestPortfolioPositions:
    def test_change_position_adds_and_reduces_and_validates_zero(self, portfolio_stub):
        holding = FakeAsset(5, "ABC")
        portfolio_stub.content["ABC"] = holding

        portfolio_stub.change_position("ABC", 2)
        portfolio_stub.change_position("ABC", -3)

        assert holding.quantity == 4
        with pytest.raises(ValueError, match="cannot be zero"):
            portfolio_stub.change_position("ABC", 0)

    def test_reduce_position_reports_missing_and_excess_quantity(self, portfolio_stub):
        portfolio_stub.content["ABC"] = FakeAsset(2, "ABC")

        assert portfolio_stub.reduce_position("XYZ", 1) == "Product 'XYZ' not found in portfolio"
        assert "fewer quantity" in portfolio_stub.reduce_position("ABC", 3)
        assert portfolio_stub.content["ABC"].quantity == 2

    def test_create_modified_copy_does_not_mutate_original(self, portfolio_stub, monkeypatch):
        original = FakeAsset(3, "ABC")
        portfolio_stub.content["ABC"] = original
        monkeypatch.setattr(Portfolio, "_create_empty_copy", lambda self: copy_stub(self))

        modified = portfolio_stub.create_modified_copy("ABC", -1)

        assert original.quantity == 3
        assert modified.content["ABC"].quantity == 2
        assert modified.content["ABC"] is not original

    def test_position_validation_rejects_invalid_changes(self, portfolio_stub):
        portfolio_stub.content["ABC"] = FakeAsset(2, "ABC")

        with pytest.raises(ValueError, match="cannot be zero"):
            portfolio_stub._validate_position_change("ABC", 0)
        with pytest.raises(ValueError, match="not found"):
            portfolio_stub._validate_position_change("XYZ", -1)
        with pytest.raises(ValueError, match="below zero"):
            portfolio_stub._validate_position_change("ABC", -3)

    def test_calculate_runs_each_calculation_stage(self, portfolio_stub, monkeypatch):
        calls = []
        for name in (
            "_convert_asset_fx", "_calculate_history", "_calculate_returns",
            "_calculate_annualized_returns", "_calculate_correlation_matrix", "_calculate_volatility",
        ):
            monkeypatch.setattr(portfolio_stub, name, lambda name=name: calls.append(name))

        portfolio_stub.calculate()

        assert len(calls) == 6

    def test_reduce_position_removes_zero_balance(self, portfolio_stub):
        portfolio_stub.content["ABC"] = FakeAsset(2, "ABC")

        assert portfolio_stub.reduce_position("ABC", 2) is None
        assert "ABC" not in portfolio_stub.content

    def test_copy_can_remove_holding_or_add_new_holding(self, portfolio_stub, monkeypatch):
        portfolio_stub.content["ABC"] = FakeAsset(2, "ABC")
        portfolio_stub.reference_assets = SimpleNamespace(
            retrieve_long_name=lambda ticker: ticker + " name",
            get_reference_asset=lambda ticker: "reference",
        )
        new_asset = FakeAsset(2, "XYZ")
        monkeypatch.setattr("backend.portfolio.portfolio.Asset", lambda *args, **kwargs: new_asset)

        removed = portfolio_stub.create_modified_copy("ABC", -2)
        added = portfolio_stub.create_modified_copy("XYZ", 2)

        assert removed.content == {}
        assert added.content == {"ABC": portfolio_stub.content["ABC"], "XYZ": new_asset}

    def test_create_empty_copy_preserves_shared_metadata(self, portfolio_stub):
        duplicate = portfolio_stub._create_empty_copy()

        assert duplicate.name == portfolio_stub.name
        assert duplicate.content == {}
        assert duplicate.fx_rates is portfolio_stub.fx_rates
        assert duplicate.reference_assets is portfolio_stub.reference_assets


class TestPortfolioHistory:
    def test_calculate_history_aligns_dates_and_adds_values(self, portfolio_stub):
        portfolio_stub.content = {
            "A": FakeAsset(1, "A", [date(2024, 1, 1), date(2024, 1, 2)], [10, 20]),
            "B": FakeAsset(1, "B", [date(2024, 1, 2), date(2024, 1, 3)], [3, 4]),
        }

        portfolio_stub._calculate_history()

        assert portfolio_stub.history["Date"].tolist() == [date(2024, 1, 2)]
        assert portfolio_stub.history["Value"].tolist() == [23]

    def test_combined_prices_use_common_dates(self, portfolio_stub):
        portfolio_stub.content = {
            "A": FakeAsset(1, "A", [date(2024, 1, 1), date(2024, 1, 2)], [10, 20]),
            "B": FakeAsset(1, "B", [date(2024, 1, 2), date(2024, 1, 3)], [3, 4]),
        }

        prices = portfolio_stub.build_combined_price_dataframe()

        assert list(prices.columns) == ["A", "B"]
        assert prices.iloc[0].tolist() == [20, 3]

    def test_correlation_matrix_and_component_serialization(self, portfolio_stub):
        dates = pd.bdate_range("2020-01-01", periods=5).date
        portfolio_stub.content = {
            "A": FakeAsset(2, "A", dates, [10, 12, 11, 13, 15]),
            "B": FakeAsset(4, "B", dates, [20, 24, 22, 26, 30]),
        }

        portfolio_stub._calculate_correlation_matrix()

        assert portfolio_stub.correlation_matrix.loc["A", "B"] == pytest.approx(1)
        assert portfolio_stub.retrieve_component_data() == {"A": 2, "B": 4}

    def test_fx_conversion_skips_eur_and_converted_assets(self, portfolio_stub, monkeypatch):
        euro = FakeAsset(1, "EUR")
        euro.fast_info = {"currency": "EUR"}
        usd = FakeAsset(1, "USD")
        usd.fast_info = {"currency": "USD"}
        usd.converted = True
        portfolio_stub.content = {"EUR": euro, "USD": usd}
        monkeypatch.setattr("backend.portfolio.portfolio.CrossFx", Mock())

        portfolio_stub._convert_asset_fx()

        assert portfolio_stub.fx_rates == {}

    def test_fx_conversion_caches_cross_rates_by_source_currency(self, portfolio_stub, monkeypatch):
        class ConvertibleAsset(FakeAsset):
            def __init__(self, ticker):
                super().__init__(1, ticker)
                self.converted = False
                self.fast_info = {"currency": "USD"}
                self.received_fx = None

            def convert_fx(self, rate):
                self.received_fx = rate
                self.converted = True

        rates = []
        monkeypatch.setattr(
            "backend.portfolio.portfolio.CrossFx",
            lambda **kwargs: rates.append(kwargs) or object(),
        )
        first, second = ConvertibleAsset("A"), ConvertibleAsset("B")
        portfolio_stub.content = {"A": first, "B": second}

        portfolio_stub._convert_asset_fx()

        assert len(rates) == 1
        assert first.received_fx is second.received_fx

    def test_calculate_returns_and_volatility_use_available_reference_periods(self, portfolio_stub):
        dates = pd.bdate_range("2018-01-01", "2024-01-01").date
        portfolio_stub.history = pd.DataFrame(
            {"Date": dates, "Value": np.linspace(100, 200, len(dates))}
        )

        portfolio_stub._calculate_returns()
        portfolio_stub._calculate_annualized_returns()
        portfolio_stub._calculate_volatility()

        assert "ytd" in portfolio_stub.returns
        assert {"1y", "3y", "5y"}.issubset(portfolio_stub.annualized_returns)
        assert {"1y", "3y", "5y"}.issubset(portfolio_stub.volatility)

    def test_percentage_change_and_reference_date_helpers(self, portfolio_stub):
        portfolio_stub.history = pd.DataFrame(
            {"Date": [date(2024, 1, 1), date(2024, 2, 1)], "Value": [100, 125]}
        )

        assert portfolio_stub._get_value_at_date(date(2024, 1, 1)) == 100
        assert portfolio_stub._calculate_percentage_change(date(2024, 2, 1), date(2024, 1, 1)) == 25
        assert portfolio_stub._get_percentage_change(date(2024, 2, 1), None) is None
        assert portfolio_stub._get_reference_date_directly(date(2023, 1, 1)) is None

    def test_compile_annualized_return_and_volatility_match_calculations(self, portfolio_stub):
        dates = pd.bdate_range("2020-01-01", periods=8).date
        portfolio_stub.history = pd.DataFrame(
            {"Date": dates, "Value": [100, 101, 103, 102, 105, 106, 108, 110]}
        )

        annualized = portfolio_stub._calculate_annualized_percentage_change(dates[-1], dates[0])
        volatility = portfolio_stub._calculate_volatility_for_a_given_period(dates[0])

        assert annualized > 0
        assert volatility > 0


class FakeAsset:
    def __init__(self, quantity, ticker, dates=None, values=None):
        dates = [date(2024, 1, 1)] if dates is None else dates
        values = [10] if values is None else values
        self.quantity = quantity
        self.ticker = ticker
        self.converted = True
        self.fast_info = {"currency": "EUR"}
        self.price_history = pd.DataFrame(
            {"Date": dates, "Price": values, "Value": values}
        )

    def change_quantity(self, change):
        self.quantity += change

    def copy_with_quantity(self, quantity):
        return FakeAsset(quantity, self.ticker, self.price_history["Date"], self.price_history["Value"])


def copy_stub(original):
    modified = object.__new__(Portfolio)
    modified.name = original.name
    modified.fx_rates = original.fx_rates
    modified.asset_names_dict = original.asset_names_dict
    modified.reference_assets = original.reference_assets
    modified.content = {}
    return modified
