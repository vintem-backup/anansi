#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ..settings import PossibleSides as Side, PossibleSignals as sig
import json
from collections import namedtuple
from functools import wraps, partial
from time import time
import pendulum
import pandas as pd


class ParseDateTime:
    fmt = "YYYY-MM-DD HH:mm:ss"

    def __init__(self, date_time_in):
        self.date_time_in = date_time_in

    def from_human_readable_to_timestamp(self):
        return pendulum.from_format(
            self.date_time_in, self.fmt, "UTC").int_timestamp

    def from_timestamp_to_human_readable(self):
        return pendulum.from_timestamp(self.date_time_in).to_datetime_string()


def seconds_in(time_frame: str) -> int:
    conversor_for = {"m": 60, "h": 3600, "d": 86400, "w": 604800}
    time_unit = time_frame[-1]
    time_amount = int(time_frame.split(time_unit)[0])

    return time_amount*conversor_for[time_unit]


class Deserialize:
    def __init__(self, name='X'):
        self.name = name

    def _json_object_hook(self, d):
        return namedtuple(self.name, d.keys())(*d.values())

    def json2obj(self, json_in):
        return json.loads(json_in, object_hook=self._json_object_hook)

    def dict2obj(self, dict_in):
        return self.json2obj(json_in=json.dumps(dict_in))


def timing(f):
    """Time to process some function f
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        _start = time()
        _result = f(*args, **kwargs)
        print(
            "Time spent on {} method: {:6.4}s".format(
                f.__name__, time() - _start))
        return _result
    return wrapper


class DocInherit(object):
    """ Docstring inheriting method descriptor

    The class itself is also used as a decorator

    Reference: <http://code.activestate.com/recipes/576862/>
    """

    def __init__(self, method):
        self.method = method
        self.name = method.__name__

    def __get__(self, obj, cls):
        if obj:
            return self.get_with_inst(obj, cls)
        else:
            return self.get_no_inst(cls)

    def get_with_inst(self, obj, cls):

        overridden = getattr(super(cls, obj), self.name, None)

        @wraps(self.method, assigned=("__name__", "__module__"))
        def f(*args, **kwargs):
            return self.method(obj, *args, **kwargs)

        return self.use_parent_doc(f, overridden)

    def get_no_inst(self, cls):

        for parent in cls.__mro__[1:]:
            overridden = getattr(parent, self.name, None)
            if overridden:
                break

        @wraps(self.method, assigned=("__name__", "__module__"))
        def f(*args, **kwargs):
            return self.method(*args, **kwargs)

        return self.use_parent_doc(f, overridden)

    def use_parent_doc(self, func, source):
        if source is None:
            raise NameError("Can't find {} in parents".format(self.name))
        func.__doc__ = source.__doc__
        return func


class FormatKlines:
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

    def format_datetime(self,
                        datetime_in,
                        truncate_seconds_to_zero=False) -> int:

        if self.DateTimeFmt == "timestamp":
            if self.DateTimeUnit == "seconds":
                datetime_out = int(float(datetime_in))

            elif self.DateTimeUnit == "milliseconds":
                datetime_out = int(float(datetime_in) / 1000)

            if truncate_seconds_to_zero:
                _date_time = pendulum.from_timestamp(int(datetime_out))

                if _date_time.second != 0:
                    datetime_out = (
                        _date_time.subtract(
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
        klines = pd.DataFrame(
            self.formatted_klines,
            columns=self.columns
        ).astype({"Open_time": "int32", "Close_time": "int32"})

        klines.attrs.update(
            {"SecondsTimeFrame": seconds_in(self.time_frame)})
        return klines


class Signal:

    def __init__(self, from_side: str, to_side: str, by_stop=False):
        self.from_side = from_side.capitalize()
        self.to_side = to_side.capitalize()
        self.by_stop = by_stop

    def get(self):
        if self.from_side == self.to_side:
            return sig.Hold

        if self.from_side == Side.Zeroed:
            if self.to_side == Side.Long:
                return sig.Buy

            if self.to_side == Side.Short:
                return sig.NakedSell

        if self.from_side == Side.Long:
            if self.to_side == Side.Zeroed:
                if self.by_stop:
                    return sig.StoppedFromLong
                return sig.Sell

            if to_side == Side.Short:
                return sig.DoubleNakedSell

        if self.from_side == Side.Short:
            if to_side == Side.Zeroed:
                if self.by_stop:
                    return sig.StoppedFromShort
                return sig.Buy

            if to_side == Side.Long:
                return sig.DoubleBuy


def get_signal(from_side, to_side, by_stop):
    return Signal(from_side, to_side, by_stop).get()


class Result:
    def __init__(self, which_side: str, by_stop=False):
        self.side = which_side
        self.by_stop = by_stop


class WarningContainer:
    def __init__(self, reporter: str, report: str = None):
        self.reporter = reporter
        self.report = report


class PrintLog(object):
    def _print_dict(self, entry):
        max_len = 30

        for item in entry.items():
            print(
                "{}{}: {}".format(item[0],
                                  "".join((max_len - len(item[0]))*["."]),
                                  item[1]))

    def print_log(self):
        kline = (
            self.last_analyzed_data.loc[
                :, self.last_analyzed_data.columns != 'Open_time'])

        print("==============================")
        print("Open_time: {}".format(
            self.last_analyzed_data.Open_time.item()))
        print("==============================")

        print(" ")
        print(kline.to_string(index=False))
        print(" ")
        print("## Analyzed_by: {} ##".format(self.analyzed_by))
        print(" ")
        self._print_dict(self.analysis_result)
        print(" ")
        print("WARNINGS:")
        self._print_dict(self._warnings_on_a_cycle)
        print(" ")
