#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import wraps, partial
from time import time


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
            raise NameError("Can't find '%s' in parents" % self.name)
        func.__doc__ = source.__doc__
        return func
