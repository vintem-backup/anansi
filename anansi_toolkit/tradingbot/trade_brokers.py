import sys


from ..settings import BinanceSettings

thismodule = sys.modules[__name__]

def trade_broker(broker_name, ticker_symbol):
    _name = broker_name.capitalize()
    return getattr(thismodule, "{}TradeBroker".format(_name))(ticker_symbol)


class BinanceTradeBroker(BinanceSettings):
    def __init__(self, ticker_symbol: str):
        self.ticker_symbol = ticker_symbol
        # ! JUST A MOCK: Only valid for BTCUSDT tests
        self.mininal_amount = self._get_mininal_amount()
        super(BinanceTradeBroker, self).__init__()

    def _get_mininal_amount(self):
        return 0.000001