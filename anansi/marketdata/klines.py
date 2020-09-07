import time
import pandas as pd
import pendulum
from . import data_brokers, indicators
from .. import settings
from ..share.tools import ParseDateTime
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
        "_since",
        "_until",
    ]

    def __init__(self, broker_name: str, symbol: str, time_frame: str = None):
        self.broker_name = broker_name.lower()
        self._broker = getattr(
            brokers, brokers.wrapper_for(self.broker_name))()
        self.symbol = symbol.upper()
        self._time_frame = time_frame
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

    def _oldest_open_time(self) -> int:
        return self._broker._oldest_open_time(
            symbol=self.symbol, time_frame=self._time_frame)

    def _request_step(self) -> int:
        return (self._broker.records_per_request *
                settings.TimeFrames().seconds_in(  # ! A função de conversão aqui, mudou
                    self._time_frame))

    def _get_raw_(self, appending_raw_to_db=False) -> pd.DataFrame:

        _table_name = "{}_{}_{}_raw".format(
            self.broker_name, self.symbol.lower(), self.time_frame)

        _Storage, klines = Storage(_table_name), pd.DataFrame()

        for timestamp in range(self._since,
                               self._until + 1,
                               self._request_step()):
            while True:
                try:
                    raw_klines = self._broker.klines(
                        self.symbol, self._time_frame, since=timestamp)

                    if appending_raw_to_db:
                        _Storage.append_dataframe(raw_klines)
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

    def _get(self, **kwargs) -> pd.DataFrame:
        _klines = self._get_raw_()

        TimeFmt = kwargs.get("TimeFmt")

        if TimeFmt == "timestamp":
            return _klines

        _klines.ParseTime.from_timestamp_to_human_readable()
        return _klines

    def period(self, since: str, until: str, **kwargs) -> pd.DataFrame:
        self._since = ParseDateTime(since).from_human_readable_to_timestamp()
        self._until = ParseDateTime(until).from_human_readable_to_timestamp()

        return self._get(**kwargs)[:-1]

    def oldest(self, number_of_candles=1, **kwargs) -> pd.DataFrame:
        self._since = self._oldest_open_time()

        _until = (number_of_candles + 1) * (
            settings.TimeFrames().seconds_in(self._time_frame)
        ) + self._since

        self._until = (_until if _until <= self._now() else self._now())

        return self._get(**kwargs)[:number_of_candles]

    def newest(self, number_of_candles=1, **kwargs) -> pd.DataFrame:
        self._until = self._now()

        _since = self._until - (number_of_candles + 1) * (
            settings.TimeFrames().seconds_in(self._time_frame))

        self._since = (_since if _since >= self._oldest_open_time()
                       else self._oldest_open_time())

        return self._get(**kwargs)[-number_of_candles:]

    def _raw_back_testing(self):
        self._since = self._oldest_open_time()
        self._until = pendulum.now(tz="UTC").int_timestamp

        # self._Storage.drop_table()
        self._get_raw_(appending_raw_to_db=True)
