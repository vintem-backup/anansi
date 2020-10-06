import time
import pandas as pd
import pendulum
from . import data_brokers as brokers
from .indicators import *
from ..share.tools import ParseDateTime, seconds_in
from ..share.db_handlers import StorageKlines

pd.options.mode.chained_assignment = None


@pd.api.extensions.register_dataframe_accessor("KlinesDateTime")
class KlinesDateTime:
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
        self.trend = Trend(self._klines)
        self.momentum = Momentum(self._klines)
        self.volatility = Volatility(self._klines)
        self.volume = Volume(self._klines)


class KlinesFromBroker:
    """ Aims to serve as a queue for requesting klines (OHLC) through brokers
    endpoints, spliting the requests, in order to respect broker established
    limits.
    If a request limit is close to being reached, will pause the queue,
    until cooldown time pass.
    Returns sanitized klines to the client, formatted as pandas DataFrame.
    """

    __slots__ = [
        "broker_name",
        "ticker_symbol",
        "_broker",
        "_time_frame",
        "_since",
        "_until",
    ]

    def __init__(self,
                 broker_name: str,
                 ticker_symbol: str,
                 time_frame: str = None):

        self.broker_name = broker_name.lower()
        self.ticker_symbol = ticker_symbol.upper()
        self._broker = getattr(
            brokers, "{}DataBroker".format(broker_name.capitalize()))()

        self._time_frame = (time_frame if time_frame
                            else "1m")  # self._broker.minimal_time_frame)
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
        return seconds_in(self._time_frame)

    def _oldest_open_time(self) -> int:
        return (
            self._broker.get_klines(
                ticker_symbol=self.ticker_symbol,
                time_frame=self._time_frame,
                since=1,
                number_of_candles=1).Open_time.item())

    def _newest_open_time(self):
        return self._now()

    def _request_step(self) -> int:
        return self._broker.records_per_request * self.SecondsTimeFrame()

    def _get_raw_(self, appending_raw_to_db=False) -> pd.DataFrame:

        table_name = "{}_{}_{}_raw".format(
            self.broker_name, self.ticker_symbol.lower(), self._time_frame)

        Storage, klines = StorageKlines(table_name), pd.DataFrame()

        for timestamp in range(self._since,
                               self._until + 1,  # 1 sec after '_until'
                               self._request_step()):
            while True:
                try:
                    raw_klines = self._broker.get_klines(
                        self.ticker_symbol, self._time_frame, since=timestamp)

                    if appending_raw_to_db:
                        Storage.append_dataframe(raw_klines)
                    klines = klines.append(raw_klines, ignore_index=True)
                    break

                except Exception as e:  # Usually connection issues.
                    # TODO: To logger instead print
                    print("Fail, due the error: ", e)
                    time.sleep(60)  # 60 sec cooldown time.

            if self._broker.was_request_limit_reached():
                time.sleep(10)  # 10 sec cooldown time.
                # TODO: To logger instead print
                print("Sleeping cause request limit was hit.")

        return klines

    # TODO: Sanitize since/until to avoid ValueError until < since
    def _until_given_since_n(self, since, number_of_candles):
        until = (number_of_candles + 1) * self.SecondsTimeFrame() + since
        self._until = (until if until <= self._now() else self._now())

    def _since_given_until_n(self, until, number_of_candles):
        since = until - (number_of_candles + 1) * self.SecondsTimeFrame()
        self._since = (since if since >= self._oldest_open_time()
                       else self._oldest_open_time())

    def _get_n_until(self, number_of_candles: int, until: int):
        self._until = until
        self._since_given_until_n(self._until, number_of_candles)
        _klines = self._get_raw_()
        return _klines[_klines.Open_time <= self._until][-number_of_candles:]

    def _get_n_since(self, number_of_candles: int, since: int):
        self._since = since
        self._until_given_since_n(self._since, number_of_candles)
        _klines = self._get_raw_()
        return _klines[_klines.Open_time >= self._since][:number_of_candles]

    def _get_given_since_and_until(self, since: int, until: int) -> pd.DataFrame:
        self._since, self._until = since, until
        _klines = self._get_raw_()
        return _klines[_klines.Open_time <= self._until]

    def _raw_back_testing(self):
        self._since = self._oldest_open_time()
        self._until = self._now()

        self._get_raw_(appending_raw_to_db=True)

    def _sanitize_input_dt(self, datetime) -> int:
        try:
            return int(datetime)  # Already int or str timestamp
        except:  # Human readable datetime ("YYYY-MM-DD HH:mm:ss")
            try:
                return (
                    ParseDateTime(
                        datetime).from_human_readable_to_timestamp())
            except:
                return 0  # indicative of error

    def get(self, **kwargs) -> pd.DataFrame:
        since = kwargs.get("since")
        until = kwargs.get("until")
        number_of_candles: int = kwargs.get("number_of_candles")

        if since:
            since = self._sanitize_input_dt(since)
        if until:
            until = self._sanitize_input_dt(until)

        klines = (
            self._get_given_since_and_until(since, until)
            if since and until and not number_of_candles
            else self._get_n_since(number_of_candles, since)
            if number_of_candles and since and not until
            else self._get_n_until(number_of_candles, until)
            if number_of_candles and until and not since
            else pd.DataFrame())  # Errors imply an empty dataframe

        klines.KlinesDateTime.from_timestamp_to_human_readable()
        return klines

    def oldest(self, number_of_candles=1) -> pd.DataFrame:
        return self.get(number_of_candles=number_of_candles,
                        since=self._oldest_open_time())

    def newest(self, number_of_candles=1) -> pd.DataFrame:
        return self.get(number_of_candles=number_of_candles,
                        until=self._now())


class BackTestingKlines(KlinesFromBroker):  # just mocking for while
    def __init__(self,
                 broker_name: str,
                 ticker_symbol: str,
                 time_frame=None):

        super(BackTestingKlines, self).__init__(
            broker_name, ticker_symbol, time_frame)


class PriceGetter:
    def __init__(self, broker_name: str, ticker_symbol: str):
        self.broker_name = broker_name
        self.ticker_symbol = ticker_symbol

    def get(self, **kwargs):
        raise NotImplementedError


class BackTestingPriceGetter:
    def __init__(self, broker_name: str, ticker_symbol: str):
        self.klines = BackTestingKlines(broker_name,
                                        ticker_symbol,
                                        time_frame="1m")

    def get(self, at: int) -> float:
        """ It's possible that the broker - due to a server side issue, 
        does not have data for the requested period, making the returned
        klines an empty dataframe. It is possible to reproduce the error
        by comment/uncomment out the 'klines' variable below. The lower
        the 'number_of_candles', the greater the possibility of an
        error. This issue will be checked in the next refactoring, when
        the klines and prices for back testing will be get from an owned
        database, after an interpolation process to complete the missing
        data.
        """

        klines = self.klines.get(number_of_candles=100, until=at+3000)
        #klines = self.klines.get(number_of_candles=10, until=at+300)
        price = klines.apply_indicator.trend.simple_moving_average(
            number_of_candles=5,
            metrics="ohlc4")
        return float(price.series.mean())
