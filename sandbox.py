from yfinance import Ticker
import matplotlib.pyplot as plt

from app.components.components import *

#int(None)

portfolio = Portfolio()
#
portfolio.add_asset("EUNL.DE", 10)
portfolio.calculate()
#

from dateutil.relativedelta import relativedelta

from datetime import date


latest_date = portfolio.history['Date'].max()
date_1_month_before = latest_date - relativedelta(months=1)
date_6_months_before = latest_date - relativedelta(months=6)
date_1_year_before = latest_date - relativedelta(years=1)
date_5_years_before = latest_date - relativedelta(years=5)
date_10_years_before = latest_date - relativedelta(years=10)
date_first_day_of_year = date(year=latest_date.year, month=1, day=1)


print((latest_date-date_1_month_before).days)

def get_actual_date(reference_date):
    df = portfolio.history[portfolio.history['Date']<=reference_date]
    number_of_rows = df.shape[0]
    if number_of_rows>0:
        return df['Date'].max()


def get_value_at_date(date):
    return portfolio.history[portfolio.history['Date']==date]['Value'].values[0]

def calculate_percentage_change(current_date, reference_date):
    current_value = get_value_at_date(current_date)
    reference_value = get_value_at_date(reference_date)
    try:
        return current_value/reference_value*100-100
    except (ZeroDivisionError, TypeError):
        return 0

#print(portfolio.history[portfolio.history['Date']==latest_date]['Value'].values[0])

def get_value_at_date():
    pass

#print(latest_date)
#print(get_actual_date(latest_date))
#print(date_1_month_before)
#print(get_actual_date(date_1_month_before))

#print(date_6_months_before)
#print(date_1_year_before)
#print(date_5_years_before)
#print(date_10_years_before)
#print(get_actual_date(date_10_years_before))
#print(date_first_day_of_year)

#print(portfolio.history)

#msci_world_etf = Asset("EUNL.DE", 10)
#print(msci_world_etf.price_history)

#portfolio.history.plot(x='Date', y='Price')
#plt.show()
#print(msci_world_etf.price_history.dtypes)
#msci_world_etf.price_history['Close'].plot(x='time', y="price")
#plt.show()


#print(msci_world_etf.info)
#msft = yf.Ticker("MSFT")

#msci_world_etf = yf.Ticker("EUNL.DE")

#print(msft.calendar)
#msftc
#print(msft['currency'])
#print(msft['marketCap'])

#print(msci_world_etf.ticker)
#print(msci_world_etf.price_history)
#
#print(hist)
#print(type(hist))
#print(hist.dtypes)


