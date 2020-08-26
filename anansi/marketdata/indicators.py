"""Todos os indicadores de mercado são reunidos aqui, estendendo a classe
pandas.Dataframe

Indicadores baseados em um preço, devem informar o 'price_source' desejado 
que, por padrão, é 'ohlc4'. Abaixo, os valores possíveis para o este parâmetro,
bem como a operação associada às colunas do dataframe de candles.

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
    __slots__ = ["name", "serie"]

    def __init__(self, name="", serie=pd.core.series.Series(dtype=float)):
        self.name = name
        self.serie = serie

    def last(self) -> float:
        return self.serie.tail(1).item()


class Price:
    __slots__ = ["_candles_dataframe"]

    def __init__(self, candles_dataframe):
        self._candles_dataframe = candles_dataframe

    def _given(self, price_source, create_indicator_column=False) -> Indicator:

        indicator = Indicator(
            name="price_{}".format(price_source),
            serie=(self._candles_dataframe[_columns[price_source]]).mean(
                axis=1),
        )
        if create_indicator_column:
            self._candles_dataframe.loc[:, indicator.name] = indicator.serie
        return indicator


class Trend:
    """Indicadores de tendência
    """

    __slots__ = ["_candles_dataframe"]

    def __init__(self, candles_dataframe):

        self._candles_dataframe = candles_dataframe

    def simple_moving_average(
        self,
        number_of_candles: int,
        price_source="ohlc4",
        create_indicator_column=False,
    ) -> Indicator:

        indicator = Indicator(
            name="sma_{}_{}".format(price_source, str(number_of_candles)),
            serie=(self._candles_dataframe.apply_indicator.price._given(price_source))
            .serie.rolling(window=number_of_candles)
            .mean(),
        )
        if create_indicator_column:
            self._candles_dataframe.loc[:, indicator.name] = indicator.serie
        return indicator


class Momentum:
    def __init__(self, candles_dataframe):

        self._candles_dataframe = candles_dataframe


class Volatility:
    def __init__(self, candles_dataframe):

        self._candles_dataframe = candles_dataframe


class Volume:
    def __init__(self, candles_dataframe):

        self._candles_dataframe = candles_dataframe
