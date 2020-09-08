from .. import settings
from ..share.tools import (
    DocInherit as doc_inherit, ConvertTimeFrame)
import pandas as pd
import requests
import pendulum


def wrapper_for(broker_name: str) -> str:
    _brokers = {
        "binance": "BinanceDataWrapper",
    }
    return _brokers[broker_name.lower()]


def get_response(endpoint: str) -> requests.models.Response:
    with requests.get(endpoint) as response:
        if response.status_code == 200:
            return response


def remove_last_if_unclosed(klines):
    last_open_time = klines[-1:].Open_time.item()
    delta_time = (pendulum.now(tz="UTC")).int_timestamp - last_open_time
    unclosed = bool(delta_time < klines.attrs["SecondsTimeFrame"])

    if unclosed:
        return klines[:-1]
    return klines


class KlinesPreFormat:
    __slots__ = [
        "time_frame",
        "DateTimeFmt",
        "DateTimeUnit",
        "columns",
        "formatted_klines",
    ]

    def __init__(
        self, time_frame,
        klines: list,
        DateTimeFmt: str,
        DateTimeUnit: str,
        columns: list
    ):

        self.time_frame = time_frame
        self.DateTimeFmt = DateTimeFmt
        self.DateTimeUnit = DateTimeUnit
        self.columns = columns
        self.formatted_klines = [self.format_each(kline) for kline in klines]

    def format_datetime(self, datetime_in, truncate_seconds_to_zero=False) -> int:
        if self.DateTimeFmt == "timestamp":
            if self.DateTimeUnit == "seconds":
                datetime_out = int(float(datetime_in))
            elif self.DateTimeUnit == "milliseconds":
                datetime_out = int(float(datetime_in) / 1000)

            if truncate_seconds_to_zero:
                _date_time = pendulum.from_timestamp(int(datetime_out))
                if _date_time.second != 0:
                    datetime_out = (
                        _date_time.subtract(seconds=_date_time.second)
                    ).int_timestamp

        return datetime_out

    def format_each(self, kline: list) -> list:

        return [
            self.format_datetime(_item, truncate_seconds_to_zero=True)
            if kline.index(_item) == self.columns.index("Open_time")
            else self.format_datetime(_item)
            if kline.index(_item) == self.columns.index("Close_time")
            else float(_item)
            for _item in kline
        ]

    def to_dataframe(self) -> pd.DataFrame:
        klines = pd.DataFrame(
            self.formatted_klines,
            columns=self.columns
        ).astype({"Open_time": "int32", "Close_time": "int32"})

        klines.attrs.update(
            {"SecondsTimeFrame": ConvertTimeFrame(
                self.time_frame).to_seconds()})
        return klines


class DataBroker:

    def server_time(self) -> int:
        """Data e horário do servidor da corretora

        Returns:
            int: Timestamp em segundos
        """
        raise NotImplementedError

    def was_request_limit_reached(self) -> bool:
        """Teste booleano para verificar se o limite de requests, no
        minuto corrente e um IP, foi atingido; utilizando a informação
        'x-mbx-used-weight-1m' (ou similar) do header do response da
        corretora, retorna o número de requests feitos no minuto
        corrente.

        Returns: bool: Limite atingido?
        """
        raise NotImplementedError

    def klines(
        self,
        symbol: str,
        time_frame: str,
        ignore_opened_candle: bool = True,
        show_only_desired_info: bool = True,
        **kwargs
    ) -> pd.DataFrame:
        """ Histórico (OHLCV) de mercado.

        Args:
            symbol (str): Símbolo do ativo
            time_frame (str): Intervalo (escala) dos candlesticks
            ignore_opened_candle (bool, optional): Defaults to True
            show_only_desired_info (bool, optional): Defaults to True.

        **kwargs:
            number_of_candles (int): Número de candelesticks
            desejados por série; observar limite de cada corretora
            ao implementar o método.

            É possível passar os timestamps, medidos em segundos:
            since (int): Open_time do primeiro candlestick da série
            until (int): Open_time do último candlestick da série

        Returns:
            pd.DataFrame: Dataframe de N linhas em que N é o número
            de amostras (klines) retornadas no response, podendo ser
            menor ou igual ao parâmetro _LIMIT_PER_REQUEST, definido
            nas configurações da corretora (arquivo settings.py).
            As colunas do dataframe representam as informações
            tabuladas pela corretora, declaradas no parâmetro
            kline_information_map, também nas configurações.
        """

        raise NotImplementedError


class BinanceDataWrapper(DataBroker, settings.Binance_):
    @doc_inherit
    def __init__(self):
        super(BinanceDataWrapper, self).__init__()

    @doc_inherit
    def server_time(self) -> int:
        return int(
            float((get_response(self._time_endpoint)).json()
                  ["serverTime"]) / 1000
        )

    @doc_inherit
    def was_request_limit_reached(self) -> bool:
        requests_on_current_minute = int(
            (get_response(self._ping_endpoint)).headers["x-mbx-used-weight-1m"]
        )
        if requests_on_current_minute >= self._request_weight_per_minute:
            return True

        return False

    @doc_inherit
    def klines(
        self,
        symbol: str,
        time_frame: str,
        ignore_opened_candle: bool = True,
        show_only_desired_info: bool = True,
        **kwargs
    ) -> pd.DataFrame:

        since: int = kwargs.get("since")
        until: int = kwargs.get("until")
        number_of_candles: int = kwargs.get("number_of_candles")
        endpoint = self._klines_endpoint.format(symbol, time_frame)

        if since:
            endpoint += "&startTime={}".format(str(since * 1000))
        if until:
            endpoint += "&endTime={}".format(str(until * 1000))
        if number_of_candles:
            endpoint += "&limit={}".format(str(number_of_candles))
        raw_klines = (get_response(endpoint)).json()

        klines = KlinesPreFormat(
            time_frame,
            raw_klines,
            DateTimeFmt=self.DateTimeFmt,
            DateTimeUnit=self.DateTimeUnit,
            columns=self.kline_informations,
        ).to_dataframe()

        if ignore_opened_candle:
            klines = remove_last_if_unclosed(klines)

        if show_only_desired_info:
            return klines[settings.kline_desired_informations]
        return klines
