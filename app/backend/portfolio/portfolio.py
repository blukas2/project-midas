import json
from datetime import date
from dateutil.relativedelta import relativedelta
from typing import Optional

from backend.globals.config import CURRENCY, ASSET_NAMES_FILE
from backend.portfolio.components import Asset, CrossFx


class Portfolio:
    def __init__(self, name: Optional[str] = None):
        self.name = name
        self.content: dict[str,Asset] = {}
        self.fx_rates: dict[str, CrossFx] = {}
        self.asset_names_dict = self._load_asset_name_dictionary()

    def _load_asset_name_dictionary(self) -> dict[str, str]:
        try:
            with open(ASSET_NAMES_FILE) as file:
                return json.load(file)
        except Exception:
            return {}

    def add_asset(self, ticker: str, quantity: int):
        if quantity<0:
            raise ValueError("Quantity cannot be added !")
        if ticker in self.content:
                self.content[ticker].change_quantity(quantity)
        else:
            long_name = self._retrieve_long_name(ticker)
            self.content[ticker] = Asset(ticker, quantity, long_name=long_name)

    def _retrieve_long_name(self, ticker: str) -> Optional[str]:
        try:
            return self.asset_names_dict[ticker]
        except KeyError:
            return None

    def reduce_position(self, ticker: str, quantity: int):
        if ticker not in self.content:
            return f"Product '{ticker}' not found in portfolio"
        elif quantity>self.content[ticker].quantity:
            return f"Unable to reduce position for '{ticker}', has fewer quantity."
        elif quantity==self.content[ticker].quantity:
            self.content.pop(ticker)
        else:
            self.content[ticker].change_quantity(-quantity)

    def calculate(self):
        self._convert_asset_fx()
        self._calculate_history()
        self._calculate_returns()
        self._calculate_annualized_returns()
        self._calculate_correlation_matrix()
        self._calculate_volatility()

    def _convert_asset_fx(self):
        for asset in self.content.values():
            if (asset.fast_info['currency']!= CURRENCY) and (asset.converted is False):
                fx_ticker = asset.fast_info['currency'] + CURRENCY
                if fx_ticker not in self.fx_rates:
                    self.fx_rates[fx_ticker] = CrossFx(target_fx=CURRENCY, source_fx=asset.fast_info['currency'])
                asset.convert_fx(self.fx_rates[fx_ticker])

    def _calculate_history(self):
        counter = 0
        for asset in self.content.values():
            counter += 1
            if counter == 1:
                self.history = asset.price_history[['Date', 'Value']]
            else:
                self.history = self.history.join(asset.price_history[['Date', 'Value']].set_index('Date'), on=['Date'], how='inner', rsuffix='_new')
                self.history['Value'] = self.history['Value'] + self.history['Value_new']
                self.history = self.history.drop(columns=['Value_new'])
        self.history = self.history.dropna()
    
    def _calculate_returns(self):
        latest_date = self.history['Date'].max()
        reference_dates = self._get_all_reference_dates(latest_date)
        self.returns = self._compile_returns_data(latest_date, reference_dates)
    
    def _calculate_annualized_returns(self):
        latest_date = self.history['Date'].max()
        reference_dates = self._get_all_reference_dates_for_annualized_returns(latest_date)
        self.annualized_returns = self._compile_returns_data(latest_date, reference_dates, annualized=True)
        
    def _compile_returns_data(self, latest_date: date, reference_dates: dict[str, date], annualized = False) -> dict[str, float]:
        returns_data = {}
        for date_string, reference_date in reference_dates.items():
            percentage_change = self._get_percentage_change(latest_date, reference_date, annualized=annualized)
            if percentage_change is not None:
                returns_data[date_string] = percentage_change
        return returns_data
    
    def _get_percentage_change(self, latest_date: date, reference_date: date, annualized=False):
        if reference_date is not None:
            if annualized:
                percentage_change = self._calculate_annualized_percentage_change(latest_date, reference_date)
            else:
                percentage_change = self._calculate_percentage_change(latest_date, reference_date) 
        else:
            percentage_change = None
        return percentage_change

    def _get_all_reference_dates_for_annualized_returns(self, latest_date) -> dict[str, date]:
        return {
            '1y': self._get_reference_date(latest_date, relativedelta(years=1)),
            '3y': self._get_reference_date(latest_date, relativedelta(years=3)),
            '5y': self._get_reference_date(latest_date, relativedelta(years=5)),
            '10y': self._get_reference_date(latest_date, relativedelta(years=10))
        }

    def _get_all_reference_dates(self, latest_date) -> dict[str, date]:
        return {
            '1m': self._get_reference_date(latest_date, relativedelta(months=1)),
            '3m': self._get_reference_date(latest_date, relativedelta(months=3)),
            '6m': self._get_reference_date(latest_date, relativedelta(months=6)),
            '1y': self._get_reference_date(latest_date, relativedelta(years=1)),
            '3y': self._get_reference_date(latest_date, relativedelta(years=3)),
            'ytd': self._get_reference_date_directly(date(year=latest_date.year, month=1, day=1))
        }

    def _get_reference_date(self, latest_date: date, reference_period: relativedelta) -> Optional[date]:
        raw_reference_date = latest_date - reference_period
        return self._get_reference_date_directly(raw_reference_date)
        
    def _get_reference_date_directly(self, raw_reference_date: date) -> Optional[date]:
        df = self.history[self.history['Date']<=raw_reference_date]
        number_of_rows = df.shape[0]
        if number_of_rows>0:
            return df['Date'].max()
        
    def _calculate_annualized_percentage_change(self, current_date: date, reference_date: date) -> float:
        percentage_change = self._calculate_percentage_change(current_date, reference_date)
        days_difference = current_date - reference_date
        years_difference = days_difference.days/365
        return ((1+percentage_change/100)**(1/years_difference))*100-100
        
    def _calculate_percentage_change(self, current_date: date, reference_date: date) -> float:
        current_value = self._get_value_at_date(current_date)
        reference_value = self._get_value_at_date(reference_date)
        try:
            return round(current_value/reference_value*100-100, 2)
        except (ZeroDivisionError, TypeError):
            return 0
    
    def _get_value_at_date(self, date) -> float:
        return self.history[self.history['Date']==date]['Value'].values[0]
    
    def retrieve_component_data(self):
        component_data = {}
        for ticker, asset in self.content.items():
            component_data[ticker] = asset.quantity
        return component_data
    
    def _calculate_correlation_matrix(self):
        counter = 1
        for ticker, asset in self.content.items():
            df_temp = asset.price_history[['Date', 'Price']].copy(deep=True)
            df_temp[ticker] = df_temp['Price']
            df_temp = df_temp.drop(columns=['Price'])
            if counter == 1:
                df = df_temp
            else:
                df = df.join(df_temp.set_index('Date'), on=['Date'], how='inner')
            counter += 1
        self.correlation_matrix = df.drop(columns=['Date']).corr()

    def _calculate_volatility(self):
        latest_date = self.history['Date'].max()
        reference_dates = self._get_all_reference_dates_for_annualized_returns(latest_date)
        self.volatility = {}
        for key, reference_date in reference_dates.items():
            if self.history[self.history['Date']==reference_date].shape[0]>0:                
                self.volatility[key] = self._calculate_volatility_for_a_given_period(reference_date)

    def _calculate_volatility_for_a_given_period(self, reference_date: date) -> float:
        filtered_df = self.history[self.history['Date']>=reference_date]
        average_value = filtered_df['Value'].mean(skipna=True)
        number_of_time_periods = filtered_df['Value'].count()
        filtered_df['diff_squared_to_average'] = (filtered_df['Value']/average_value-1)**2
        sum_of_diff_squared = filtered_df['diff_squared_to_average'].sum(skipna=True)
        standard_deviation = (sum_of_diff_squared/number_of_time_periods)**(1/2)
        volatility = standard_deviation*(number_of_time_periods**(1/2))
        return volatility
