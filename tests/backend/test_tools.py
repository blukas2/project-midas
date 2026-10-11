import json
from types import SimpleNamespace

import pandas as pd
import pytest

from backend import tools
from backend.tools import AssetFinder, AssetSearchResult, FileManager


class TestFileManager:
    def test_save_portfolio_writes_component_quantities(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tools, "PORTFOLIOS_FOLDER", str(tmp_path))
        manager = FileManager()
        manager.folder = str(tmp_path)
        portfolio = SimpleNamespace(name="Growth (custom)", retrieve_component_data=lambda: {"ABC": 3})

        manager.save_portfolio(portfolio)

        assert json.loads((tmp_path / "Growth.json").read_text()) == {"ABC": 3}

    def test_load_custom_portfolio_calculates_assets(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tools, "Portfolio", lambda name: FakePortfolio(name))
        manager = FileManager()
        manager.folder = str(tmp_path)
        (tmp_path / "Growth.json").write_text('{"ABC": 3}')

        result = manager._load_custom_porfolio("Growth (custom)")

        assert result.name == "Growth (custom)"
        assert result.assets == [("ABC", 3)]

    def test_load_portfolio_calculates_and_returns_custom_portfolio(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tools, "Portfolio", lambda name: FakePortfolio(name))
        manager = FileManager()
        manager.folder = str(tmp_path)
        (tmp_path / "Growth.json").write_text('{"ABC": 3}')

        result = manager.load_portfolio("Growth (custom)")

        assert result.assets == [("ABC", 3)]
        assert result.calculated is True

    def test_latest_file_is_selected_by_filename_date(self, monkeypatch):
        monkeypatch.setattr(tools.os, "listdir", lambda path: ["export_2023-01-01.csv", "export_2024-02-03.csv"])
        manager = FileManager()
        manager.folder = "unused"

        assert manager._get_latest_portfolio_filename("fund") == "export_2024-02-03.csv"

    def test_read_portfolio_data_converts_localized_quantity_and_joins_asset_names(self, monkeypatch):
        monkeypatch.setattr(tools, "PORTFOLIOS_FOLDER", "portfolio-root")
        monkeypatch.setattr(tools, "ROOT_FOLDER", "app-root")
        monkeypatch.setattr(
            tools.pd, "read_csv",
            lambda path, **kwargs: pd.DataFrame(
                {"ISIN": ["DE0001"], "Titel": ["Fund"], "Menge": ["1.234,00"]}
            ) if "portfolio-root" in path else pd.DataFrame(
                {"isin": ["DE0001"], "ticker": ["ABC"]}
            ),
        )

        result = FileManager()._read_portfolio_data("fund", "file.csv")

        assert result.loc[0, "quantity"] == 1234
        assert result.loc[0, "ticker"] == "ABC"

    def test_date_parser_and_search_quote_defaults(self):
        manager = FileManager()
        quote = AssetFinder()._parse_quote({"symbol": "ABC", "shortname": "Company"})

        assert manager._get_date_value_from_filename("export_2024-02-03.csv") == 20240203
        assert (quote.ticker, quote.long_name, quote.asset_type) == ("ABC", "Company", "N/A")
        assert repr(AssetSearchResult("ABC", "Company", "ETF")) == "ABC - Company (ETF)"

    def test_finder_uses_yfinance_results(self, monkeypatch):
        monkeypatch.setattr(tools.yf, "Search", lambda query: SimpleNamespace(quotes=[{"symbol": query}]))

        assert AssetFinder().find_assets("ABC")[0].ticker == "ABC"

    def test_list_portfolio_names_maps_custom_and_directory_entries(self, tmp_path, monkeypatch):
        manager = FileManager()
        manager.folder = str(tmp_path)
        (tmp_path / "Custom.json").write_text("{}")
        (tmp_path / "Portfolio").mkdir()
        monkeypatch.setattr(tools.os, "listdir", lambda path: ["Custom.json", "Portfolio"])

        manager.list_portfolio_names()

        assert manager.portfolio_names_list == ["Custom (custom)", "Portfolio"]

    def test_list_portfolio_names_rejects_invalid_entry(self, monkeypatch):
        manager = FileManager()
        manager.folder = "unused"
        monkeypatch.setattr(tools.os, "listdir", lambda path: ["invalid.txt"])

        with pytest.raises(ValueError, match="Invalid portfolio item"):
            manager.list_portfolio_names()


class FakePortfolio:
    def __init__(self, name):
        self.name = name
        self.assets = []

    def add_asset(self, ticker, quantity):
        self.assets.append((ticker, quantity))

    def calculate(self):
        self.calculated = True
