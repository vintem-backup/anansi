class Binance(object):
    def __init__(self, ticker_symbol: str):
        self.ticker_symbol = ticker_symbol

    def mininal_amount(self):
        return 0.000001  # ! JUST A MOCK: Válido apenas paras os testes BTCUSDT
