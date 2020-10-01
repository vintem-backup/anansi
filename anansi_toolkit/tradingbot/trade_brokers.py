from ..settings import BinanceSettings


class BinanceOrderBroker(BinanceSettings):
    def __init__(self, ticker_symbol: str):
        self.ticker_symbol = ticker_symbol
        # ! JUST A MOCK: Only valid for BTCUSDT tests
        self.mininal_amount = self._get_mininal_amount()
        super(BinanceOrderBroker, self).__init__()

    def _get_mininal_amount(self):
        return 0.000001
