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

    def define_side(self):
        print(self.data_to_analyze[-1:])
