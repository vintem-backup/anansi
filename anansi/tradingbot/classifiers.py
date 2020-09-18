import json
from ..share import tools
deserialize = tools.Deserialize()


class CrossSMA:
    class DefaultParameters:
        def __init__(self):
            # TODO: Create classes 'PossiblePriceSource' and
            # 'PossibleTimeFrames' on settings module
            self.time_frame = "6h"
            self.price_source = "ohlc4"
            self.smaller_sample = 3
            self.larger_sample = 80

    def __init__(self, parameters, data_to_analyze=None):
        self.parameters = deserialize.json2obj(parameters)
        self.data_to_analyze = data_to_analyze
        self.n_samples_to_analyze = self.parameters.larger_sample

    def result(self):
        side = "short"
        self.data_to_analyze.apply_indicator.price._given(
            price_source=self.parameters.price_source,
            indicator_column="price_{}".format(self.parameters.price_source))

        smaller_SMA = (
            self.data_to_analyze.apply_indicator.trend.simple_moving_average(
                number_of_candles=self.parameters.smaller_sample,
                price_source=self.parameters.price_source,
                indicator_column="smaller_SMA"))

        larger_SMA = (
            self.data_to_analyze.apply_indicator.trend.simple_moving_average(
                number_of_candles=self.parameters.larger_sample,
                price_source=self.parameters.price_source,
                indicator_column="larger_SMA"))

        if smaller_SMA.last() > larger_SMA.last():
            side = "long"

        return (self.data_to_analyze[-1:]).assign(suggested_side=side)
