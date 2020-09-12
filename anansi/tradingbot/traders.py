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
            self.klines.time_frame = self.Classifier.parameters.time_frame
            self._now = self.klines._oldest_open_time()
            self.operation.position.update_current_side_to(side.Zeroed)

    def run(self):
        while self.operation.status == stat.Running:
            self._do_analysis()
            self._loop()

        self._end()

    def _loop(self):
        if self.operation.mode == mode.BackTesting:
            self._now += self._step
        else:
            time.sleep(self._step)
            self._now = pendulum.now().int_timestamp

    def _do_analysis(self):
        if (not self.operation.ignore_stop_loss) and (
                self.operation.position.current_side != side.Zeroed):
            # self._step =
            self.stop_analysis()
        else:
            # self._step =
        self.classifier_analysis()

    def stop_analysis(self):
        pass

    def classifier_analysis(self):
        pass
