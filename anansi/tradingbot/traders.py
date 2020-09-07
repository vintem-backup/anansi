from marketdata import klines
import pendulum
from .order_handler import *


class Logger:
    pass


class OperationalReport:
    pass


class DefaultTrader:

    def __init__(self, Operation):

        self.Operation = Operation
        self._now = pendulum.now().int_timestamp
        self.Operation.status == "Running"

        self.Logger = Logger()

        self.Classifier = getattr(
            classifiers, self.Operation.classifier_name)(
                self.Operation.classifier_parameters)

        self.StopLoss = getattr(
            stop_handlers, self.Operation.stop_loss_name)(
                self.Operation.stop_loss_parameters)

        self.KStreamer = klines.FromBroker(  # Por hora, evocando da corretora
            broker_name=self.Operation.exchange,
            symbol=self.Operation.symbol
        )

        self.OrderHandler = OrderHandler(
            broker_name=self.Operation.exchange,
            symbol=self.Operation.symbol)

        if self.mode == "BackTesting":
            self.Logger.level = "DEBUG"
            self.KStreamer.time_frame = (
                self.Operation.Classifier.parameters.time_frame)

            self._now = self.KStreamer.oldest(
                number_of_candles=1).Open_time  # .to_timestamp
