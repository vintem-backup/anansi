import time
import pandas as pd
import pendulum
from . import (data_brokers as brokers,
               indicators)
from .. import settings
from ..share.tools import ParseDateTime, ConvertTimeFrame
from ..share.db_handlers import StorageKlines


@pd.api.extensions.register_dataframe_accessor("ParseTime")
class ParseTime:
    def __init__(self, klines: pd.DataFrame):
        self._klines = klines

    def from_human_readable_to_timestamp(self):
        self._klines.loc[:, "Open_time"] = self._klines.apply(
            lambda date_time: ParseDateTime(
                date_time["Open_time"]
            ).from_human_readable_to_timestamp(),
            axis=1,
        )

        if "Close_time" in self._klines:
            self._klines.loc[:, "Close_time"] = self._klines.apply(
                lambda date_time: ParseDateTime(
                    date_time["Close_time"]
                ).from_human_readable_to_timestamp(),
                axis=1,
            )

    def from_timestamp_to_human_readable(self):
        self._klines.loc[:, "Open_time"] = self._klines.apply(
            lambda date_time: ParseDateTime(
                date_time["Open_time"]
            ).from_timestamp_to_human_readable(),
            axis=1,
        )

        if "Close_time" in self._klines:
            self._klines.loc[:, "Close_time"] = self._klines.apply(
                lambda date_time: ParseDateTime(
                    date_time["Close_time"]
                ).from_timestamp_to_human_readable(),
                axis=1,
            )


@pd.api.extensions.register_dataframe_accessor("apply_indicator")
class ApplyIndicator:
    def __init__(self, klines):
        self._klines = klines
        self.price = indicators.Price(self._klines)
        self.trend = indicators.Trend(self._klines)
        self.momentum = indicators.Momentum(self._klines)
        self.volatility = indicators.Volatility(self._klines)
        self.volume = indicators.Volume(self._klines)


class FromBroker:
    """Tem por finalidade servir de fila para a solicitação de klines às
    corretoras, dividindo o número de requests a fim de respeitar os limites
    das mesmas e interrompendo os pedidos caso este limite esteja próximo de
    ser atingido, entregando ao cliente os candles sanitizados e formatados.
    """

    __slots__ = [
        "broker_name",
        "_broker",
        "symbol",
        "_time_frame",
        "_ForceTimestampFormat",
        "_since",
        "_until",
    ]

    def __init__(self, broker_name: str, symbol: str, time_frame: str = None):
        self.broker_name = broker_name.lower()
        self._broker = getattr(
            brokers, brokers.wrapper_for(self.broker_name))()
        self.symbol = symbol.upper()
        self._time_frame = time_frame
        self._ForceTimestampFormat = False
        self._since = 1
        self._until = 2

    @property
    def time_frame(self):
        return self._time_frame

    @time_frame.setter
    def time_frame(self, time_frame_to_set):
        self._time_frame = time_frame_to_set

    def _now(self) -> int:
        return (pendulum.now(tz="UTC")).int_timestamp

    def SecondsTimeFrame(self):
        return ConvertTimeFrame(self._time_frame).to_seconds()

    def _oldest_open_time(self) -> int:
        return (
            self._broker.get_klines(
                symbol=self.symbol,
                time_frame=self._time_frame,
                since=1,
                number_of_candles=1).Open_time.item())

    def _request_step(self) -> int:
        return self._broker.records_per_request * self.SecondsTimeFrame()

    def _get_raw_(self, appending_raw_to_db=False) -> pd.DataFrame:

        table_name = "{}_{}_{}_raw".format(
            self.broker_name, self.symbol.lower(), self._time_frame)

        Storage, klines = StorageKlines(table_name), pd.DataFrame()

        for timestamp in range(self._since,
                               self._until + 1,
                               self._request_step()):
            while True:
                try:
                    raw_klines = self._broker.get_klines(
                        self.symbol, self._time_frame, since=timestamp)

                    if appending_raw_to_db:
                        Storage.append_dataframe(raw_klines)
                    klines = klines.append(raw_klines, ignore_index=True)
                    break

                except Exception as e:
                    # TODO: To logger instead print
                    print("Fail, due the error: ", e)
                    time.sleep(60)

            if self._broker.was_request_limit_reached():
                time.sleep(10)
                # TODO: To logger instead print
                print("Sleeping cause request limit was hit.")

        return klines

    def _get(self) -> pd.DataFrame:
        _klines = self._get_raw_()
        if self._ForceTimestampFormat:
            return _klines

        _klines.ParseTime.from_timestamp_to_human_readable()
        return _klines

    def _until_given(self, since, number_of_candles):
        until = (number_of_candles + 1) * self.SecondsTimeFrame() + since
        self._until = (until if until <= self._now() else self._now())

    def _since_given(self, until, number_of_candles):
        since = until - (number_of_candles + 1) * self.SecondsTimeFrame()
        self._since = (since if since >= self._oldest_open_time()
                       else self._oldest_open_time())

    def _get_n_until(self, number_of_candles: int, until: int):
        self._until = until
        self._since_given(self._until, number_of_candles)
        return self._get()[-number_of_candles:]

    def _get_n_since(self, number_of_candles: int, since: int):
        self._since = since
        self._until_given(self._since, number_of_candles)
        return self._get()[:number_of_candles]

    def _get_given_since_and_until(self, since: str, until: str) -> pd.DataFrame:
        self._since = ParseDateTime(since).from_human_readable_to_timestamp()
        self._until = ParseDateTime(until).from_human_readable_to_timestamp()

        return self._get()[:-1]

    def _raw_back_testing(self):
        self._since = self._oldest_open_time()
        self._until = self._now()

        # self._Storage.drop_table()
        self._get_raw_(appending_raw_to_db=True)

    def get(self):
        pass

    def oldest(self, number_of_candles=1) -> pd.DataFrame:
        return self._get_n_since(
            number_of_candles, since=self._oldest_open_time())

    def newest(self, number_of_candles=1) -> pd.DataFrame:
        return self._get_n_until(number_of_candles, until=self._now())
