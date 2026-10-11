import pandas as pd
import pytest
import requests

from backend.portfolio import components
from backend.portfolio.components import Asset, CrossFx


class TestAsset:
    def test_constructor_loads_price_history_without_network(self, monkeypatch):
        history = pd.DataFrame({"Date": [pd.Timestamp("2024-01-01")], "Price": [10]})
        monkeypatch.setattr(Asset, "_get_price_history", lambda self: history)
        asset = Asset("ABC", 2, long_name="Alpha")

        assert asset.ticker == "ABC"
        assert asset.quantity == 2
        assert asset.price_history is history
        assert asset.converted is False

    def test_change_quantity_rejects_negative_position(self):
        asset = Asset.__new__(Asset)
        asset.quantity = 2

        with pytest.raises(ValueError, match="cannot be decreased"):
            asset.change_quantity(-3)
        asset.change_quantity(-2)
        assert asset.quantity == 0

    def test_copy_with_quantity_is_independent(self):
        asset = Asset.__new__(Asset)
        asset.quantity = 2
        asset.price_history = pd.DataFrame({"Price": [10], "Value": [20], "Quantity": [2]})

        clone = asset.copy_with_quantity(5)
        clone.price_history.loc[0, "Price"] = 100

        assert clone.price_history.loc[0, "Value"] == 50
        assert asset.price_history.loc[0, "Price"] == 10
        assert clone.quantity == 5

    def test_get_longname_uses_cached_name_or_info_then_ticker(self, monkeypatch):
        named = Asset.__new__(Asset)
        named.long_name = "Alpha"
        assert named.get_longname() == "Alpha"

        monkeypatch.setattr(Asset, "info", property(lambda self: {"longName": "Beta"}), raising=False)
        unnamed = Asset.__new__(Asset)
        unnamed.long_name = None
        unnamed.ticker = "XYZ"
        assert unnamed.get_longname() == "Beta"

        def failed_info(self):
            raise requests.exceptions.HTTPError("offline")

        monkeypatch.setattr(Asset, "info", property(failed_info), raising=False)
        assert unnamed.get_longname() == "XYZ"

    def test_price_history_filters_zero_volume_and_calculates_values(self, monkeypatch):
        asset = Asset.__new__(Asset)
        asset.quantity = 2
        asset.reference_asset = None
        monkeypatch.setattr(Asset, "fast_info", property(lambda self: {"currency": "EUR"}), raising=False)
        monkeypatch.setattr(Asset, "ticker", "ABC", raising=False)
        raw = pd.DataFrame(
            {"Close": [5.0, 10.0], "Volume": [1, 0]},
            index=pd.DatetimeIndex(["2024-01-01", "2024-01-02"], name="Date"),
        )
        monkeypatch.setattr(Asset, "history", lambda self, **kwargs: raw)

        with pytest.warns(pd.errors.SettingWithCopyWarning):
            actual = asset._get_price_history()

        assert actual["Price"].tolist() == [5.0]
        assert actual["Value"].tolist() == [10.0]
        assert actual["Currency"].tolist() == ["EUR"]

    def test_convert_fx_preserves_original_prices_and_converts_value(self):
        asset = Asset.__new__(Asset)
        asset.converted = False
        asset.price_history = pd.DataFrame(
            {
                "Date": [pd.Timestamp("2024-01-01").date()],
                "Price": [10.0],
                "Value": [20.0],
            }
        )
        fx = type("Fx", (), {
            "price_history": pd.DataFrame(
                {"Date": [pd.Timestamp("2024-01-01").date()], "FX Rate": [2.0]}
            )
        })()

        asset.convert_fx(fx)

        assert asset.converted is True
        assert asset.price_history.loc[0, "Price"] == 5
        assert asset.price_history.loc[0, "Value"] == 10
        assert asset.price_history.loc[0, "Price Original Fx"] == 10


class TestCrossFx:
    def test_constructor_formats_pair_and_loads_history(self, monkeypatch):
        expected_history = pd.DataFrame({"FX Rate": [1.1]})
        monkeypatch.setattr(components.Ticker, "__init__", lambda self, ticker: setattr(self, "ticker", ticker))
        monkeypatch.setattr(CrossFx, "_get_price_history", lambda self: expected_history)

        fx = CrossFx("EUR", "USD")

        assert fx.ticker == "EURUSD=X"
        assert fx.price_history is expected_history

    def test_price_history_renames_and_converts_dates(self, monkeypatch):
        fx = CrossFx.__new__(CrossFx)
        raw = pd.DataFrame(
            {"Close": [1.1]}, index=pd.DatetimeIndex(["2024-01-01"], name="Date")
        )
        monkeypatch.setattr(CrossFx, "history", lambda self, **kwargs: raw)

        actual = fx._get_price_history()

        assert actual.loc[0, "FX Rate"] == 1.1
        assert actual.loc[0, "Date"].isoformat() == "2024-01-01"
