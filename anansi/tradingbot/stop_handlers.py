import json
from ..share import tools
#convert = tools.ConvertTimeFrame
deserialize = tools.Deserialize()


class Treshold:
    def __init__(self, n_measurements: int, n_positives: int):
        self.n_measurements = n_measurements
        self.n_positives = (n_positives if n_positives <=
                            n_measurements else n_measurements)


class Trigger:
    def __init__(self, rate: float, treshold: Treshold):
        self.rate = rate
        self.treshold = treshold


class StopTrailing3T:
    class DefaultParameters:
        def __init__(self):

            self.time_frame = "1m"
            self.price_source = "ohlc4"

            self.first_trigger = Trigger(
                rate=10,
                treshold=Treshold(n_measurements=5, n_positives=3))

            self.second_trigger = Trigger(
                rate=3,
                treshold=Treshold(n_measurements=60, n_positives=20))

            self.third_trigger = Trigger(
                rate=1,
                treshold=Treshold(n_measurements=120, n_positives=40))

            self.update_target_if = Trigger(
                rate=0.7,
                treshold=Treshold(n_measurements=10, n_positives=3))

    def __init__(self, operation):
        self.operation = operation

        if not self.operation.stop_loss_parameters:
            self.operation.update_stop_loss_parameters_to(
                json.dumps(self.DefaultParameters(),
                           default=lambda o: o.__dict__, indent=4)
            )

        self.parameters = deserialize.json2obj(
            self.operation.stop_loss_parameters)

    def how_many_candles(self) -> int:
        return max(
            self.parameters.first_trigger.treshold.n_measurements,
            self.parameters.second_trigger.treshold.n_measurements,
            self.parameters.third_trigger.treshold.n_measurements,
            self.parameters.update_target_if.treshold.n_measurements,
        )
