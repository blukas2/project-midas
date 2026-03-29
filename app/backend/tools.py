import os
import json
import logging
import pandas as pd
from pandas import DataFrame

import yfinance as yf

from backend.globals.config import ROOT_FOLDER, PORTFOLIOS_FOLDER
from backend.portfolio.portfolio import Portfolio

logger = logging.getLogger(__name__)


class FileManager:
    def __init__(self):
        self.folder = PORTFOLIOS_FOLDER
    
    def save_portfolio(self, portfolio: Portfolio):        
        component_data = portfolio.retrieve_component_data()
        file_name = portfolio.name.replace(" (custom)", "") + '.json'
        file_path = f"{self.folder}/{file_name}"
        with open(file_path, mode="w+") as file:
            file.write(json.dumps(component_data))

    def load_portfolio(self, portfolio_name: str):
        if portfolio_name.endswith(" (custom)"):
            portfolio = self._load_custom_porfolio(portfolio_name)
        else:
            portfolio = self._load_original_portfolio(portfolio_name)
        portfolio.calculate()
        return portfolio
    
    def _load_custom_porfolio(self, portfolio_name: str) -> Portfolio:
        file_name = portfolio_name.replace(" (custom)", "") + ".json"
        file_path = f"{self.folder}/{file_name}"
        with open(file_path) as file:
            component_data = json.load(file)
        portfolio = Portfolio(portfolio_name)
        for ticker, quantity in component_data.items():
            portfolio.add_asset(ticker, quantity)
        return portfolio

    def _load_original_portfolio(self, portfolio_name: str) -> Portfolio:
        file_name = self._get_latest_portfolio_filename(portfolio_name)
        portfolio_df = self._read_portfolio_data(portfolio_name, file_name)
        portfolio_items = portfolio_df.to_dict(orient="records")
        portfolio = Portfolio(portfolio_name)
        for item in portfolio_items:
            try:
                portfolio.add_asset(item["ticker"], item["quantity"])
            except Exception as e:
                logger.error("Error adding %s to portfolio %s.", item['ticker'], portfolio_name)
                raise e
        return portfolio

    def _get_latest_portfolio_filename(self, portfolio_name: str) -> str:
        portfolio_files = os.listdir(f"{self.folder}/{portfolio_name}")
        portfolio_dates_and_files = {
            self._get_date_value_from_filename(filename): filename 
            for filename in portfolio_files
        }
        latest_date = max(portfolio_dates_and_files.keys())
        file_name = portfolio_dates_and_files[latest_date]
        return file_name

    def _get_date_value_from_filename(self, filename: str):
        filename_wo_extension = filename.split(".")[0]
        date_text = filename_wo_extension.split("_")[-1]
        date_value = int(date_text.replace("-", ""))
        return date_value
    
    def _read_portfolio_data(self, portfolio_name: str, file_name: str) -> DataFrame:
        portfolio_df = pd.read_csv(f"{PORTFOLIOS_FOLDER}/{portfolio_name}/{file_name}", sep=";", encoding="utf-16")
        portfolio_df.rename(
            columns={
                "ISIN": "isin",
                "Titel": "name",
                "Menge": "quantity"
            }, inplace=True)
        portfolio_df = portfolio_df[["isin", "name", "quantity"]]
        portfolio_df["quantity"] = (
            portfolio_df["quantity"]
            .str.replace(".", "").str.replace(",", ".")
            .astype(float).astype(int)
        )
        asset_names_df = pd.read_csv(f"{ROOT_FOLDER}/asset_names.csv", sep=";", encoding="ISO-8859-1")
        portfolio_df = portfolio_df.merge(asset_names_df, on="isin", how="left")
        logger.debug("Loaded portfolio data with %d assets.", len(portfolio_df))
        return portfolio_df

    def list_portfolio_names(self):
        names_list = []
        for item_name in os.listdir(self.folder):
            if item_name.endswith(".json"):
                names_list.append(item_name.replace(".json", "") + " (custom)")
            elif "." not in item_name:
                names_list.append(item_name)
            else:
                raise ValueError("Invalid portfolio item.")                
        self.portfolio_names_list = names_list


class AssetSearchResult:
    """Represents a single found asset with its ticker and name."""

    def __init__(self, ticker: str, long_name: str, asset_type: str):
        self.ticker = ticker
        self.long_name = long_name
        self.asset_type = asset_type

    def __repr__(self) -> str:
        return f"{self.ticker} - {self.long_name} ({self.asset_type})"


class AssetFinder:
    """Finds financial asset tickers by searching long names and symbols."""

    def find_assets(self, query: str) -> list[AssetSearchResult]:
        """Search for assets matching the query by name or ticker."""
        search = yf.Search(query)
        return self._parse_results(search.quotes)

    def _parse_results(self, quotes: list[dict]) -> list[AssetSearchResult]:
        """Parse raw search quotes into AssetSearchResult objects."""
        return [self._parse_quote(quote) for quote in quotes]

    def _parse_quote(self, quote: dict) -> AssetSearchResult:
        """Parse a single quote dictionary into an AssetSearchResult."""
        return AssetSearchResult(
            ticker=quote.get("symbol", "N/A"),
            long_name=quote.get("longname", quote.get("shortname", "N/A")),
            asset_type=quote.get("quoteType", "N/A"),
        )
