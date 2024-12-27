from pandas import DataFrame
from datetime import date
from dateutil.relativedelta import relativedelta
from typing import Optional

class ReturnsCalculator:
    def __init__(self):
        pass

    def calculate_returns(self, history: DataFrame, source_column: str):
        self.history = history
        self.source_column = source_column
        latest_date = self.history['Date'].max()
        reference_dates = self._get_all_reference_dates(latest_date)
        returns = self._compile_returns_data(latest_date, reference_dates)
        return returns
    
    def calculate_annualized_returns(self, history: DataFrame, source_column: str):
        self.history = history
        self.source_column = source_column
        latest_date = self.history['Date'].max()
        reference_dates = self._get_all_reference_dates_for_annualized_returns(latest_date)
        annualized_returns = self._compile_returns_data(latest_date, reference_dates, annualized=True)
        return annualized_returns
        
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
        return self.history[self.history['Date']==date][self.source_column].values[0]

    def calculate_volatility(self, history: DataFrame, source_column: str):
        self.history = history
        self.source_column = source_column
        latest_date = self.history['Date'].max()
        reference_dates = self._get_all_reference_dates_for_annualized_returns(latest_date)
        volatility = {}
        for key, reference_date in reference_dates.items():
            if self.history[self.history['Date']==reference_date].shape[0]>0:                
                volatility[key] = self._calculate_volatility_for_a_given_period(reference_date)
        return volatility

    def _calculate_volatility_for_a_given_period(self, reference_date: date) -> float:
        filtered_df = self.history[self.history['Date']>=reference_date]
        average_value = filtered_df[self.source_column].mean(skipna=True)
        number_of_time_periods = filtered_df[self.source_column].count()
        filtered_df['diff_squared_to_average'] = (filtered_df[self.source_column]/average_value-1)**2
        sum_of_diff_squared = filtered_df['diff_squared_to_average'].sum(skipna=True)
        standard_deviation = (sum_of_diff_squared/number_of_time_periods)**(1/2)
        volatility = standard_deviation#*(number_of_time_periods**(1/2))
        return volatility
    
