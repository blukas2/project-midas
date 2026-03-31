from __future__ import annotations

from pandas import DataFrame

from backend.portfolio.components import Asset, CrossFx
from backend.globals.calculators import ReturnsCalculator
from backend.globals.config import CURRENCY

from typing import Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from backend.portfolio.portfolio import Portfolio


class Comparer:
    def __init__(self):
        self.returns_calculator = ReturnsCalculator()
        self._portfolio_position: Optional[int] = None
        self._portfolio_history: Optional[DataFrame] = None

    def compare(self, ticker1, ticker2):
        self._portfolio_position = None
        self._portfolio_history = None
        self.asset1 = Asset(ticker1, 1)
        self.asset2 = Asset(ticker2, 1)
        self.asset1_name = self.asset1.get_longname()
        self.asset2_name = self.asset2.get_longname()
        self.asset1_eur = self._prepare_eur_copy(self.asset1)
        self.asset2_eur = self._prepare_eur_copy(self.asset2)
        self.recalculate(in_eur=True)

    def compare_with_portfolio(self, portfolio: Portfolio, other_ticker: str, portfolio_position: int):
        """Compare portfolio against an asset. portfolio_position is 1 or 2."""
        self._portfolio_position = portfolio_position
        self._portfolio_history = portfolio.history.rename(columns={'Value': 'Price'})
        portfolio_name = portfolio.name or "Portfolio"
        other_asset = Asset(other_ticker, 1)
        other_name = other_asset.get_longname()
        other_asset_eur = self._prepare_eur_copy(other_asset)
        if portfolio_position == 1:
            self.asset1_name = portfolio_name
            self.asset2_name = other_name
            self.asset1, self.asset2 = None, other_asset
            self.asset1_eur, self.asset2_eur = None, other_asset_eur
        else:
            self.asset1_name = other_name
            self.asset2_name = portfolio_name
            self.asset1, self.asset2 = other_asset, None
            self.asset1_eur, self.asset2_eur = other_asset_eur, None
        self.recalculate(in_eur=True)

    def recalculate(self, in_eur: bool):
        """Rebuild comparison tables using EUR or native-currency histories."""
        history1 = self._get_asset_history(1, in_eur)
        history2 = self._get_asset_history(2, in_eur)
        self._build_compare_table(history1, history2)
        self._calculate_price_indicies()
        self._calculate_annualized_returns()
        self._calculate_volatility()

    def _get_asset_history(self, position: int, in_eur: bool) -> DataFrame:
        """Return the price history for the given asset position."""
        is_portfolio = self._portfolio_position == position
        if is_portfolio:
            return self._portfolio_history
        asset = self.asset1 if position == 1 else self.asset2
        asset_eur = self.asset1_eur if position == 1 else self.asset2_eur
        if in_eur and asset_eur is not None:
            return asset_eur.price_history
        return asset.price_history

    def _prepare_eur_copy(self, asset: Asset) -> Optional[Asset]:
        """Create an EUR-converted copy of the asset if its native currency differs."""
        native_currency = asset.fast_info['currency']
        if native_currency == CURRENCY:
            return None
        cross_fx = CrossFx(target_fx=CURRENCY, source_fx=native_currency)
        eur_copy = Asset(asset.ticker, 1)
        eur_copy.convert_fx(cross_fx)
        return eur_copy

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
