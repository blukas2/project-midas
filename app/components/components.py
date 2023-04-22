import pandas as pd
from yfinance import Ticker
from datetime import date
from dateutil.relativedelta import relativedelta


class Asset(Ticker):
    def __init__(self, ticker: str, quantity: int, session=None):
        super().__init__(ticker, session)
        self.quantity = quantity
        self.price_history = self._get_price_history()

    def _get_price_history(self):
        df = self.history(period="15y")
        df = df[df['Volume']!=0]
        df['Currency'] = self.info['currency']
        df['Quantity'] = self.quantity
        df = df.rename(columns={'Close': 'Price'})
        df['Value'] = df['Price']*self.quantity
        df.reset_index(inplace=True)
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        return df

    def change_quantity(self, quantity_change):
        if self.quantity + quantity_change < 0:
            raise ValueError("The quantity of an asset cannot be decreased by more than its current quantity")
        self.quantity = self.quantity + quantity_change


class Portfolio:
    def __init__(self):
        self.content: dict[str,Asset] = {}

    def add_asset(self, ticker: str, quantity: int):
        if quantity<0:
            raise ValueError("Quantity cannot be added !")
        if ticker in self.content:
                self.content[ticker].change_quantity(quantity)
        else:
            self.content[ticker] = Asset(ticker, quantity)

    def reduce_position(self, ticker: str, quantity: int):
        if ticker not in self.content:
            raise ValueError(f"Product '{ticker}' not found in portfolio")
        if quantity>self.content[ticker].quantity:
            raise ValueError(f"Unable to reduce position for '{ticker}', has fewer quantity.")
        if quantity==self.content[ticker].quantity:
            self.content.pop(ticker)
        else:
            self.content[ticker].change_quantity(-quantity)

    def calculate(self):
        self._calculate_history()

    def _calculate_history(self):
        for asset in self.content.values():
            self.history = asset.price_history[['Date', 'Price', 'Value']]
            break

    def _calculate_returns(self):
        latest_date = self.history['Date'].max()
        reference_dates = self._get_all_reference_dates(latest_date)

    def _get_all_reference_dates(self, latest_date):
        return {
            '1m': self._get_reference_date(latest_date, relativedelta(months=1)),
            '6m': self._get_reference_date(latest_date, relativedelta(months=6)),
            '1y': self._get_reference_date(latest_date, relativedelta(years=1)),
            '5y': self._get_reference_date(latest_date, relativedelta(years=5)),
            '10y': self._get_reference_date(latest_date, relativedelta(years=10)),
            'ytd': self._get_reference_date_directly(date(year=latest_date.year, month=1, day=1))
        }

    def _get_reference_date(self, latest_date: date, reference_period: relativedelta):
        raw_reference_date = latest_date - reference_period
        return self._get_reference_date_directly(raw_reference_date)
        
    def _get_reference_date_directly(self, raw_reference_date: date):
        df = self.history[self.history['Date']<=raw_reference_date]
        number_of_rows = df.shape[0]
        if number_of_rows>0:
            return df['Date'].max()
        
    def _calculate_annualized_percentage_change(self, current_date: date, reference_date: date):
        percentage_change = self._calculate_percentage_change(current_date, reference_date)
        days_difference = current_date - reference_date
        years_difference = days_difference.days/365
        return (1+percentage_change)**(1/years_difference)-1
        
    def _calculate_percentage_change(self, current_date: date, reference_date: date):
        current_value = self._get_value_at_date(current_date)
        reference_value = self._get_value_at_date(reference_date)
        try:
            return current_value/reference_value-1
        except (ZeroDivisionError, TypeError):
            return 0
    
    def _get_value_at_date(self, date):
        return self.history[self.history['Date']==date]['Value'].values[0]

    

    



    