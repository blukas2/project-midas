from __future__ import annotations

from datetime import date
from dateutil.relativedelta import relativedelta

from pandas import DataFrame

from backend.tools import AssetFinder, AssetSearchResult
from backend.portfolio.components import Asset, CrossFx
from backend.globals.calculators import ReturnsCalculator
from backend.globals.config import CURRENCY

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from backend.portfolio.portfolio import Portfolio


class AssetAnalyzer:
    """Loads a single asset and provides price history and annualized returns."""

    def __init__(self):
        self.asset_finder = AssetFinder()
        self.returns_calculator = ReturnsCalculator()
        self.asset: Asset | None = None
        self.asset_eur: Asset | None = None
        self.native_currency: str = ""

    def search(self, query: str) -> list[AssetSearchResult]:
        """Search for assets matching the query text."""
        return self.asset_finder.find_assets(query)

    def load_asset(self, ticker: str):
        """Load an asset by ticker and prepare EUR-converted data if needed."""
        self.asset = Asset(ticker, 1)
        self.native_currency = self.asset.fast_info['currency']
        self._prepare_eur_conversion()

    def get_price_history(self, in_eur: bool) -> DataFrame:
        """Return price history for the last 5 years (or full available period)."""
        history = self._get_history_table(in_eur)
        cutoff_date = date.today() - relativedelta(years=5)
        filtered = history[history['Date'] >= cutoff_date]
        if filtered.empty:
            return history[['Date', 'Price']].copy()
        return filtered[['Date', 'Price']].copy()

    def get_annualized_returns(self, in_eur: bool) -> dict[str, float]:
        """Calculate annualized returns using the price history."""
        history = self.get_price_history(in_eur)
        return self.returns_calculator.calculate_annualized_returns(history, 'Price')

    def get_indexed_price_history(self, in_eur: bool) -> DataFrame:
        """Return price history indexed to 100 at start of period."""
        history = self.get_price_history(in_eur).copy()
        base_price = history['Price'].iloc[0]
        history['Asset'] = history['Price'] / base_price * 100
        return history[['Date', 'Asset']]

    def get_portfolio_indexed_history(self, portfolio: Portfolio) -> DataFrame:
        """Return portfolio history indexed to 100, aligned to asset's date range."""
        asset_history = self.get_price_history(in_eur=True)
        min_date = asset_history['Date'].min()
        portfolio_hist = portfolio.history[portfolio.history['Date'] >= min_date].copy()
        if portfolio_hist.empty:
            return DataFrame(columns=['Date', 'Portfolio'])
        base_value = portfolio_hist['Value'].iloc[0]
        portfolio_hist['Portfolio'] = portfolio_hist['Value'] / base_value * 100
        return portfolio_hist[['Date', 'Portfolio']]

    def get_currency_label(self, in_eur: bool) -> str:
        """Return the currency label for chart display."""
        if in_eur:
            return CURRENCY
        return self.native_currency

    def _prepare_eur_conversion(self):
        """Create an EUR-converted copy of the asset if native currency differs."""
        if self.native_currency == CURRENCY:
            self.asset_eur = None
            return
        cross_fx = CrossFx(target_fx=CURRENCY, source_fx=self.native_currency)
        self.asset_eur = Asset(self.asset.ticker, 1)
        self.asset_eur.convert_fx(cross_fx)

    def _get_history_table(self, in_eur: bool) -> DataFrame:
        """Select the appropriate price history based on currency toggle."""
        if in_eur and self.asset_eur is not None:
            return self.asset_eur.price_history
        return self.asset.price_history
