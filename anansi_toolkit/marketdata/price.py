class PriceGetter:
    def __init__(self, broker_name: str, ticker_symbol: str):
        self.broker_name = broker_name
        self.ticker_symbol = ticker_symbol

    def get(self, **kwargs):
        raise NotImplementedError


class BackTestingPriceGetter:
    def __init__(self, broker_name: str, ticker_symbol: str):
        self.klines = BackTestingKlines(
            broker_name, ticker_symbol, time_frame="1m"
        )

    def get(self, at: int) -> float:
        """It's possible that the broker - due to a server side issue,
        does not have data for the requested period, making the returned
        klines an empty dataframe. It is possible to reproduce the error
        by comment/uncomment out the 'klines' variable below. The lower
        the 'number_of_candles', the greater the possibility of an
        error. This issue will be checked in the next refactoring, when
        the klines and prices for back testing will be get from an owned
        database, after an interpolation process to complete the missing
        data.
        """

        klines = self.klines.get(number_of_candles=100, until=at + 3000)
        # klines = self.klines.get(number_of_candles=10, until=at+300)
        price = klines.apply_indicator.trend.simple_moving_average(
            number_of_candles=5, metrics="ohlc4"
        )
        return float(price._series.mean())