""" All market indicators are coded here, extending the pandas.Dataframe
object, using default pandas API on 'handlers' module.

Indicators based on assets prices, must inform the desired 'metrics'
which, by default, is 'ohlc4'. Below, the possible values ​​for this
parameter, as well as the associated calculation.

"o"     = "Open"
"h"     = "High"
"l"     = "Low"
"c"     = "Close"
"oh2"   = ("Open" + "High")/2
"olc3"  = ("Open" + "Low" + "Close")/3
"ohlc4" = ("Open" + "High" + "Low" + "Close")/4
"""

import pandas as pd

_columns = {
    "o": ["Open"],
    "h": ["High"],
    "l": ["Low"],
    "c": ["Close"],
    "hl2": ["High", "Low"],
    "hlc3": ["High", "Low", "Close"],
    "ohlc4": ["Open", "High", "Low", "Close"],
}


class Indicator(object):
    __slots__ = ["name", "_series"]

    def __init__(self, name="", _series=pd.core.series.Series(dtype=float)):
        self.name = name
        self._series = _series

    def last(self) -> float:
        return self._series.tail(1).item()


@pd.api.extensions.register_dataframe_accessor("PriceFromKline")
class PriceFromKline:
    __slots__ = ["_klines"]

    def __init__(self, klines: pd.DataFrame):
        self._klines = klines

    def using(self, metrics: str, **kwargs) -> Indicator:
        indicator_column = kwargs.get("indicator_column")

        indicator = Indicator(
            name="price_{}".format(metrics),
            _series=(self._klines[_columns[metrics]]).mean(
                axis=1))

        if indicator_column:
            self._klines.loc[:, indicator_column] = indicator.series
        return indicator


class Trend:
    __slots__ = ["_klines"]

    def __init__(self, klines):
        self._klines = klines

    def simple_moving_average(self, number_of_candles: int,
                              metrics="ohlc4", **kwargs) -> Indicator:

        indicator_column = kwargs.get("indicator_column")

        indicator = Indicator(
            name="sma_{}_{}".format(metrics, str(number_of_candles)),
            _series=(self._klines.PriceFromKline.using(metrics))
            ._series.rolling(window=number_of_candles).mean())

        if indicator_column:
            self._klines.loc[:, indicator_column] = indicator.series
        return indicator


class Momentum:
    def __init__(self, klines):

        self._klines = klines


class Volatility:
    def __init__(self, klines):

        self._klines = klines


class Volume:
    def __init__(self, klines):

        self._klines = klines
