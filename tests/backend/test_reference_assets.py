import pandas as pd

from backend import portfolio
from backend.portfolio import reference_assets
from backend.portfolio.reference_assets import ReferenceAssets


class TestReferenceAssets:
    def test_metadata_is_indexed_and_null_reference_returns_none(self, monkeypatch):
        frame = pd.DataFrame(
            {"ticker": ["ABC", "XYZ"], "long_name": ["Alpha", None], "reference_ticker": ["REF", None]}
        )
        monkeypatch.setattr(reference_assets.pd, "read_csv", lambda *args, **kwargs: frame)
        monkeypatch.setattr(reference_assets, "Asset", lambda ticker, quantity: (ticker, quantity))
        assets = ReferenceAssets()

        assert assets.retrieve_long_name("ABC") == "Alpha"
        assert assets.retrieve_long_name("missing") == "missing"
        assert assets.retrieve_reference_ticker("XYZ") is None
        assert assets.get_reference_asset("XYZ") is None

    def test_reference_asset_is_cached(self, monkeypatch):
        monkeypatch.setattr(
            reference_assets.pd, "read_csv",
            lambda *args, **kwargs: pd.DataFrame(
                {"ticker": ["ABC"], "long_name": ["Alpha"], "reference_ticker": ["REF"]}
            ),
        )
        created = []
        monkeypatch.setattr(reference_assets, "Asset", lambda ticker, quantity: created.append(ticker) or object())
        assets = ReferenceAssets()

        first = assets.get_reference_asset("ABC")
        second = assets.get_reference_asset("ABC")

        assert first is second
        assert created == ["REF"]
