from ..settings import PossibleSides as Side
import json
from ..share.tools import Result, Deserialize
deserialize = Deserialize()


class CrossSMA:
    class DefaultParameters:
        def __init__(self):
            self.time_frame = "6h"
            self.price_metrics = "ohlc4"
            self.smaller_sample = 3
            self.larger_sample = 80

    def __init__(self, parameters, log, data_to_analyze=None):
        self._indicators_dict = {}
        self._side = None
        self._price = None
        self._SMA_smaller = None
        self._SMA_larger = None
        self.parameters = deserialize.json2obj(parameters)
        self.log = log
        self.data_to_analyze = data_to_analyze
        self.n_samples_to_analyze = self.parameters.larger_sample

    def _make_indicators_dict(self):
        self._indicators_dict = {
            "Price ({})".format(self.parameters.price_metrics):
            self._price.last(),

            "SMA_smaller ({} candles)".format(
                self.parameters.smaller_sample): self._SMA_smaller.last(),

            "SMA_larger ({} candles)".format(
                self.parameters.larger_sample): self._SMA_larger.last(),
        }

    def _consolidate_log(self):
        self.log.analyzed_by = "Classifier"
        self.log.last_analyzed_data = self.data_to_analyze[-1:]
        self.log.analysis_result = {
            **self._indicators_dict, "side": self._side}

    def result(self):
        self._side = Side.Short
        self._price = self.data_to_analyze.PriceFromKline.using(
            self.parameters.price_metrics)

        self._SMA_smaller = (
            self.data_to_analyze.apply_indicator.trend.simple_moving_average(
                number_of_candles=self.parameters.smaller_sample,
                metrics=self.parameters.price_metrics))

        self._SMA_larger = (
            self.data_to_analyze.apply_indicator.trend.simple_moving_average(
                number_of_candles=self.parameters.larger_sample,
                metrics=self.parameters.price_metrics))

        if self._SMA_smaller.last() > self._SMA_larger.last():
            self._side = Side.Long

        self._make_indicators_dict()
        self._consolidate_log()

        return Result(self._side)
