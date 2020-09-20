#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from collections import namedtuple
from functools import wraps, partial
from time import time
import pendulum


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


class ConvertTimeFrame:
    seconds_dict = {
        "1m": 60,
        "3m": 180,
        "5m": 300,
        "15m": 900,
        "30m": 1800,
        "1h": 3600,
        "2h": 7200,
        "4h": 14400,
        "6h": 21600,
        "12h": 43200,
        "1d": 86400,
        "1w": 604800,
    }

    def __init__(self, time_frame):
        self.time_frame = time_frame

    def to_seconds(self):
        return self.seconds_dict[self.time_frame]


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


class Printers(object):
    def print_dict(self, entry):
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
        print("## RESULTS FROM {} ##".format(self.results_from))
        print(" ")
        self.print_dict(self.analysis_result)
        print(" ")
        print(" ")
