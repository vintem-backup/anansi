from . import classifiers
from ..marketdata import klines
import pendulum
from .order_handler import *
from ..settings import (PossibleSides as side,
                        PossibleStatuses as stat, PossibleModes as mode)


class Logger:
    def __init__(self, operation):
        self.operation = operation


class operationalReport:
    pass


class Movement:
    signal = None
    base_asset_amount = None
    timestamp = None
    price = None
    fee = None


class DefaultTrader:

    def __init__(self, operation):

        self.operation = operation
        self._now = pendulum.now().int_timestamp
        self.operation.update_status_to(stat.Running)

        self.logger = Logger(operation=self.operation)

        self.Classifier = getattr(
            classifiers, self.operation.classifier_name)(
                operation=self.operation)

        # self.StopLoss = getattr(
        #    stop_handlers, self.operation.stop_loss_name)(
        #        operation=self.operation)

        self.klines = klines.FromBroker(  # Por hora, evocando da corretora
            broker_name=self.operation.exchange,
            symbol=self.operation.symbol
        )

        self.OrderHandler = OrderHandler(operation=self.operation)

        if self.operation.mode == mode.BackTesting:

            self.klines.time_frame = (
                self.Classifier.parameters.time_frame)

            self._now = self.klines._oldest_open_time()
