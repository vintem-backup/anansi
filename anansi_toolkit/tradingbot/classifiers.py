from ..settings import PossibleSides as SIDE
import json
from ..share.tools import Serialize, Deserialize, seconds_in
deserialize = Deserialize()


class Result:
    side = SIDE.Zeroed
    due_to_stop = False


class CrossSMA:
    class DefaultParameters:
        def __init__(self):
            self.time_frame = "6h"
            self.price_metrics = "ohlc4"
            self.smaller_sample = 3
            self.larger_sample = 80
    
    def __init__(self, parameters, log):
        self.parameters = deserialize.from_json(parameters)
        self.log = log
        self.analyzed_data = None
        self.number_of_candles = self.parameters.larger_sample
        self.step = seconds_in(self.parameters.time_frame)

    def _append_to_log(self, data, result):
        self.log.analyzed_by = self.__class__.__name__
        self.log.analysis_result = Serialize(result).to_dict()
        self.log.last_analyzed_data = (data.to_dict(orient="records")[0])

    def get_result_for_this(self, data):
        result = Result()

        result.SMA_smaller = (
            data.apply_indicator.trend.simple_moving_average(
                number_of_candles=self.parameters.smaller_sample,
                metrics=self.parameters.price_metrics)).last()

        result.SMA_larger = (
            data.apply_indicator.trend.simple_moving_average(
                number_of_candles=self.parameters.larger_sample,
                metrics=self.parameters.price_metrics)).last()

        result.side = (
            SIDE.Long if result.SMA_smaller > result.SMA_larger
            else SIDE.Zeroed)
        
        data.KlinesDateTime.from_human_readable_to_timestamp()
        self._append_to_log(data[-1:], result)
        return result
