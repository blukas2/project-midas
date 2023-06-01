from pandas import DataFrame

from backend.portfolio.components import Asset
from backend.globals.calculators import ReturnsCalculator

class Comparer:
    def __init__(self):
        self.returns_calculator = ReturnsCalculator()

    def compare(self, ticker1, ticker2):
        self.asset1 = Asset(ticker1, 1)
        self.asset2 = Asset(ticker2, 1)
        self.asset1_name = self.asset1.info['longName']
        self.asset2_name = self.asset2.info['longName']
        self._create_compare_table()
        self._calculate_price_indicies()
        self._calculate_annualized_returns()
        self._calculate_volatility()

    def _create_compare_table(self):
        asset1_table = self._get_asset_price_table(self.asset1.price_history, 'asset1')
        asset2_table = self._get_asset_price_table(self.asset2.price_history, 'asset2')
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
