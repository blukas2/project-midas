from yfinance import Ticker


class Asset(Ticker):
    def __init__(self, ticker: str, quantity: float, session=None):
        super().__init__(ticker, session)
        self.quantity = quantity
        self.price_history = self._get_price_history()

    def _get_price_history(self):
        df = self.history(period="15y")
        df = df[df['Volume']!=0]
        df['Value'] = df['Close']*self.quantity
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