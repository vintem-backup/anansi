from ..settings import PossibleSides as Side
import json
from ..share.tools import Serialize, Deserialize
deserialize = Deserialize()


class Result:
    by_stop = False


class CrossSMA:
    class DefaultParameters:
        def __init__(self):
            self.time_frame = "6h"
            self.price_metrics = "ohlc4"
            self.smaller_sample = 3
            self.larger_sample = 80

    def __init__(self, parameters, log, data_to_analyze=None):
        self.parameters = deserialize.from_json(parameters)
        self.log = log
        self.data_to_analyze = data_to_analyze
        self.n_samples_to_analyze = self.parameters.larger_sample
        self.result = Result()

    def _log_it(self):
        _last_analyzed_data = self.data_to_analyze[-1:]
        _last_analyzed_data.KlinesDateTime.from_human_readable_to_timestamp()

        self.log.analysis_result = Serialize(self.result).to_dict()
        self.log.analyzed_by = self.__class__.__name__
        self.log.last_analyzed_data = (
            _last_analyzed_data.to_dict(orient="records")[0])

    def get_result(self):
        self.result.side = Side.Short

        self.result.price = self.data_to_analyze.PriceFromKline.using(
            self.parameters.price_metrics).last()

        self.result.SMA_smaller = (
            self.data_to_analyze.apply_indicator.trend.simple_moving_average(
                number_of_candles=self.parameters.smaller_sample,
                metrics=self.parameters.price_metrics)).last()

        self.result.SMA_larger = (
            self.data_to_analyze.apply_indicator.trend.simple_moving_average(
                number_of_candles=self.parameters.larger_sample,
                metrics=self.parameters.price_metrics)).last()

        if self.result.SMA_smaller > self.result.SMA_larger:
            self.result.side = Side.Long

        self._log_it()

        return self.result
