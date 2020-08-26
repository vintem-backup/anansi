import sys
try:
    sys.path.insert(0, '..')
    import settings
    import my_tools

except Exception as e:
    print(e)

import pandas as pd
import requests
import pendulum


class Broker:
    def __init__(self):
        pass

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
            ignore_opened_candle (bool, optional): [description]. Defaults to True.
            show_only_desired_info (bool, optional): [description]. Defaults to True.

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

    def _oldest_open_time(self, symbol: str, time_frame: str) -> int:
        """ Timestamp do Open_time do primeiro candle deste tipo
        (symbol e time_frame) armazenado no servidor da corretora

        Returns:
            int: Timestamp em segundos
        """
        raise NotImplementedError


doc_inherit = my_tools.DocInherit


def wrapper_for(broker_name: str) -> str:
    _brokers = {
        "binance": "BinanceApiWrapper",
    }
    return _brokers[broker_name.lower()]


def get_response(endpoint: str) -> requests.models.Response:
    with requests.get(endpoint) as response:
        if response.status_code == 200:
            return response


class Transform:
    def __init__(self,
                 klines: list,
                 DateTimeFmt: str,
                 DateTimeUnit: str,
                 columns: list):

        self.DateTimeFmt = DateTimeFmt
        self.DateTimeUnit = DateTimeUnit
        self.columns = columns
        self.formatted_klines = [self.format_each(kline)
                                 for kline in klines]

    def format_datetime(
            self,
            datetime_in,
            truncate_seconds_to_zero=False) -> int:
        if self.DateTimeFmt == 'timestamp':
            if self.DateTimeUnit == 'seconds':
                datetime_out = int(float(datetime_in))
            elif self.DateTimeUnit == 'milliseconds':
                datetime_out = int(float(datetime_in)/1000)

            if truncate_seconds_to_zero:
                _date_time = pendulum.from_timestamp(int(datetime_out))
                if _date_time.second != 0:
                    datetime_out = (_date_time.subtract(
                        seconds=_date_time.second)).int_timestamp

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
        return (
            pd.DataFrame(
                self.formatted_klines, columns=self.columns
            ).astype({'Open_time': 'int32', 'Close_time': 'int32'}))


class BinanceApiWrapper(Broker, settings.Binance_):
    @doc_inherit
    def __init__(self):
        super(BinanceApiWrapper, self).__init__()

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
        _klines = (get_response(endpoint)).json()
        if ignore_opened_candle:
            now = (pendulum.now(tz="UTC")).int_timestamp
            last_open_time = int((float(_klines[-1][0])) / 1000)
            if ((now - last_open_time)
                    < settings.TimeFrames().seconds_in(time_frame)):
                _klines = _klines[:-1]

        klines_object = Transform(_klines, DateTimeFmt=self.DateTimeFmt,
                                  DateTimeUnit=self.DateTimeUnit,
                                  columns=self.kline_information_map).to_dataframe()
        if show_only_desired_info:
            return klines_object[settings.klines_desired_info]
        return klines_object

    @ doc_inherit
    def _oldest_open_time(self, symbol: str, time_frame: str) -> int:
        return self.klines(
            symbol=symbol, time_frame=time_frame, since=1, number_of_candles=1
        ).Open_time.item()