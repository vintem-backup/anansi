import json
from ..share import tools
#convert = tools.ConvertTimeFrame
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

    def __init__(self, operation):
        self.operation = operation

        if not self.operation.classifier_parameters:
            self.operation.update_classifier_parameters_to(
                json.dumps(self.DefaultParameters(),
                           default=lambda o: o.__dict__, indent=4)
            )

        self.parameters = deserialize.json2obj(
            self.operation.classifier_parameters)

    def how_many_candles(self) -> int:
        return self.parameters.larger_sample
