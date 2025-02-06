import pandas as pd

from backend.globals.config import ROOT_FOLDER
from backend.portfolio.components import Asset

from typing import Optional


class ReferenceAssets:
    def __init__(self):
        self.asset_names_df = pd.read_csv(f"{ROOT_FOLDER}/asset_names.csv", sep=";", encoding="ISO-8859-1")
        self.asset_names_records = self.asset_names_df.to_dict(orient="records")
        self.long_name_dict = {record["ticker"]: record["long_name"] for record in self.asset_names_records}
        self.reference_ticker_dict = {record["ticker"]: record["reference_ticker"] for record in self.asset_names_records}

        self.repository: dict[str, Asset] = {}

    def retrieve_long_name(self, ticker: str) -> str:
        return self.long_name_dict.get(ticker, ticker)
    
    def retrieve_reference_ticker(self, ticker: str) -> str:
        return self.reference_ticker_dict.get(ticker)
    
    def get_reference_asset(self, ticker: str) -> Optional[Asset]:
        """Returns the reference asset for a given ticker"""
        reference_ticker = self.retrieve_reference_ticker(ticker)
        if reference_ticker:
            if reference_ticker not in self.repository:
                self.repository[reference_ticker] = Asset(reference_ticker, 1)
            return self.repository[reference_ticker]
