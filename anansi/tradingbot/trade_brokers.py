class Binance(object):
    def __init__(self, ticker_symbol: str):
        self.ticker_symbol = ticker_symbol

    def mininal_amount(self):
        return 500.0
