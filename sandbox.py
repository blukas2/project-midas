from yfinance import Ticker
import matplotlib.pyplot as plt

from app.components.components import *

#int(None)

portfolio = Portfolio()
#

from app.globals.settings import FOLDER

import os

print(os.listdir(FOLDER))
#portfolio.add_asset("EUNL.DE", 10)
#portfolio.calculate()
#print(portfolio.annualized_returns)
#print(portfolio.history)
#asset = Asset("EUNL.DE", 10)
#print(asset.info)
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


