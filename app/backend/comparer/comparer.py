from __future__ import annotations

from pandas import DataFrame

from backend.portfolio.components import Asset
from backend.globals.calculators import ReturnsCalculator

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from backend.portfolio.portfolio import Portfolio

class Comparer:
    def __init__(self):
        self.returns_calculator = ReturnsCalculator()

    def compare(self, ticker1, ticker2):
        self.asset1 = Asset(ticker1, 1)
        self.asset2 = Asset(ticker2, 1)
        self.asset1_name = self.asset1.get_longname()
        self.asset2_name = self.asset2.get_longname()
        self._build_compare_table(self.asset1.price_history, self.asset2.price_history)
        self._calculate_price_indicies()
        self._calculate_annualized_returns()
        self._calculate_volatility()

    def compare_with_portfolio(self, portfolio: Portfolio, other_ticker: str, portfolio_position: int):
        """Compare portfolio against an asset. portfolio_position is 1 or 2."""
        portfolio_history = portfolio.history.rename(columns={'Value': 'Price'})
        portfolio_name = portfolio.name or "Portfolio"
        other_asset = Asset(other_ticker, 1)
        other_name = other_asset.get_longname()
        if portfolio_position == 1:
            self.asset1_name = portfolio_name
            self.asset2_name = other_name
            self._build_compare_table(portfolio_history, other_asset.price_history)
        else:
            self.asset1_name = other_name
            self.asset2_name = portfolio_name
            self._build_compare_table(other_asset.price_history, portfolio_history)
        self._calculate_price_indicies()
        self._calculate_annualized_returns()
        self._calculate_volatility()

    def _build_compare_table(self, asset1_history: DataFrame, asset2_history: DataFrame):
        asset1_table = self._get_asset_price_table(asset1_history, 'asset1')
        asset2_table = self._get_asset_price_table(asset2_history, 'asset2')
        self.compare_table = (asset1_table
                              .join(asset2_table.set_index('Date'), on=['Date'], how='inner')
                              )

    def _get_asset_price_table(self, price_history: DataFrame, asset_nametag: str) -> DataFrame:
        asset_table = price_history[['Date', 'Price']]
        asset_table[asset_nametag + '_price'] = asset_table['Price']
        asset_table = asset_table[['Date', asset_nametag + '_price']]
        return asset_table
    
    def _calculate_price_indicies(self):
        self._calculate_price_index_for_asset('asset1')
        self._calculate_price_index_for_asset('asset2')

    def _calculate_price_index_for_asset(self, asset_nametag: str):
        asset_base = self.compare_table[asset_nametag + '_price'].iloc[0]
        self.compare_table[asset_nametag + '_price_index'] = self.compare_table[asset_nametag + '_price']/asset_base*100

    def _calculate_annualized_returns(self):
        self.asset1_annualized_returns = self.returns_calculator.calculate_annualized_returns(self.compare_table, 'asset1_price_index')
        self.asset2_annualized_returns = self.returns_calculator.calculate_annualized_returns(self.compare_table, 'asset2_price_index')

    def _calculate_volatility(self):
        self.asset1_volatility = self.returns_calculator.calculate_volatility(self.compare_table, 'asset1_price_index')
        self.asset2_volatility = self.returns_calculator.calculate_volatility(self.compare_table, 'asset2_price_index')
