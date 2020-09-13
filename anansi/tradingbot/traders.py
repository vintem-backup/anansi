import pendulum
from .order_handler import *
from . import classifiers, stop_handlers, order_handler
from ..marketdata import klines
from ..share.tools import ConvertTimeFrame
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
        self._step = None
        self.operation = operation
        self._now = pendulum.now().int_timestamp
        self.operation.update_status_to(stat.Running)
        self.logger = Logger(operation=self.operation)

        self.Classifier = getattr(
            classifiers, self.operation.classifier_name)(
                operation=self.operation)

        self.StopLoss = getattr(
            stop_handlers, self.operation.stop_loss_name)(
                operation=self.operation)

        self.step_for_Classifier = (
            ConvertTimeFrame(
                self.Classifier.parameters.time_frame).to_seconds())

        self.step_for_StopLoss = (
            ConvertTimeFrame(
                self.StopLoss.parameters.time_frame).to_seconds())

        self.KlinesGetter = klines.FromBroker(  # Por hora, evocando da corretora
            broker_name=self.operation.exchange,
            symbol=self.operation.symbol)

        self.OrderHandler = (
            order_handler.OrderHandler(operation=self.operation))

        if self.operation.mode == mode.BackTesting:
            self.KlinesGetter.time_frame = (
                self.Classifier.parameters.time_frame)

            self._now = self._initial_now_for_backtesting()

            self.operation.position.update_current_side_to(side.Zeroed)

    def _initial_now_for_backtesting(self):
        return (self.KlinesGetter._oldest_open_time()
                + (self.step_for_Classifier *
                   self.Classifier.how_many_candles()))

    def _get_ready_to_repeat(self):
        if self.operation.mode == mode.BackTesting:
            self._now += self._step
        else:
            time.sleep(self._step)
            self._now = pendulum.now().int_timestamp

    def _do_analysis(self):
        if (not self.operation.ignore_stop_loss) and (
                self.operation.position.current_side != side.Zeroed):

            self._step = self._step_for_StopLoss
            self._stop_analysis()

        else:
            self._step = self.step_for_Classifier

        self._classifier_analysis()

    def _stop_analysis(self):
        pass

    def _classifier_analysis(self):
        pass

    def run(self):
        while self.operation.status == stat.Running:
            self._do_analysis()
            self._get_ready_to_repeat()

        # self._end()
