from yfinance import Ticker
import matplotlib.pyplot as plt

from app.components.components import *

portfolio = Portfolio()

portfolio.add_asset("EUNL.DE", 10)
portfolio.calculate()

print(portfolio.history)

#msci_world_etf = Asset("EUNL.DE", 10)
#print(msci_world_etf.price_history)


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


