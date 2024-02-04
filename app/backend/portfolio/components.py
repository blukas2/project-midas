
import pandas as pd
from yfinance import Ticker
import requests

from typing import Optional


class CrossFx(Ticker):
    def __init__(self, target_fx, source_fx):
        ticker = f"{target_fx}{source_fx}=X"
        super().__init__(ticker)
        self.price_history = self._get_price_history()

    def _get_price_history(self):
        df = self.history(period="15y")
        df = df.rename(columns={'Close': 'FX Rate'})
        df.reset_index(inplace=True)
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        return df


class Asset(Ticker):
    def __init__(self, ticker: str, quantity: int, long_name: Optional[str] = None, session=None):
        super().__init__(ticker, session)
        self.quantity = quantity
        self.price_history = self._get_price_history()
        self.converted = False
        self.long_name = long_name

    def _get_price_history(self):
        df = self.history(period="15y")
        df = df[df['Volume']!=0]
        df['Currency'] = self.fast_info['currency']
        df['Quantity'] = self.quantity
        df = df.rename(columns={'Close': 'Price'})
        df['Value'] = df['Price']*self.quantity
        df.reset_index(inplace=True)
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        return df
    
    def convert_fx(self, cross_fx: CrossFx):
        self.price_history = (self.price_history
                              .join(cross_fx.price_history[['Date', 'FX Rate']]
                                    .set_index('Date'), on=['Date'], 
                                    how='left', rsuffix='_fx'))
        self.price_history['Price Original Fx'] = self.price_history['Price']
        self.price_history['Value Original Fx'] = self.price_history['Value']
        self.price_history['Price'] = self.price_history['Price']/self.price_history['FX Rate']
        self.price_history['Value'] = self.price_history['Value']/self.price_history['FX Rate']
        self.converted = True

    def change_quantity(self, quantity_change):
        if self.quantity + quantity_change < 0:
            raise ValueError("The quantity of an asset cannot be decreased by more than its current quantity")
        self.quantity = self.quantity + quantity_change

    def get_longname(self):
        if self.long_name is not None:
            return self.long_name
        else:
            try:
                return self.info['longName']
            except (requests.exceptions.HTTPError, TypeError):
                return self.ticker
