import pendulum
import pandas as pd
from .order_handler import *
from .models import Log
from . import classifiers, stop_handlers, order_handler
from ..marketdata import klines
from ..share.tools import ConvertTimeFrame
from ..settings import (
    PossibleSides as side,
    PossibleStatuses as stat,
    PossibleModes as mode,
)


class DefaultTrader:
    def __init__(self, operation):
        self.operation = operation
        self.log = Log(operation=self.operation)
        self._step = None
        self._hint_side = None

        self.Classifier = getattr(classifiers, self.operation.classifier.name)(
            parameters=self.operation.classifier.parameters
        )

        self._classifier_time_frame_in_seconds = ConvertTimeFrame(
            self.Classifier.parameters.time_frame
        ).to_seconds()

        self.StopLoss = getattr(stop_handlers, self.operation.stop_loss.name)(
            parameters=self.operation.stop_loss.parameters
        )

        self._stop_loss_time_frame_in_seconds = ConvertTimeFrame(
            self.StopLoss.parameters.time_frame
        ).to_seconds()

        self.KlinesGetter = klines.FromBroker(  # Por hora, evocando da corretora
            broker_name=self.operation.market.exchange,
            symbol=(
                self.operation.market.ticker_symbol
                + self.operation.market.quote_symbol)
        )

        self._now = (
            self._initial_now_for_backtesting()
            if self.operation.mode == mode.BackTesting
            else pendulum.now().int_timestamp
        )

        self.OrderHandler = order_handler.OrderHandler(
            operation=self.operation)

    def _initial_now_for_backtesting(self):
        self.KlinesGetter.time_frame = self.Classifier.parameters.time_frame

        return self.KlinesGetter._oldest_open_time() + (
            self._classifier_time_frame_in_seconds
            * self.Classifier.n_samples_to_analyze
        )

    def _get_ready_to_repeat(self):
        if self.operation.mode == mode.BackTesting:
            self._now += self._step
        else:
            time.sleep(self._step)
            self._now = pendulum.now().int_timestamp

    def _do_analysis(self):
        if (self.operation.stop_on) and (
            self.operation.position.side.held != side.Zeroed
        ):

            self._step = self._step_for_StopLoss
            self._stop_analysis()

        else:
            self._step = self._classifier_time_frame_in_seconds

        self._classifier_analysis()

    def _stop_analysis(self):
        print("Finally stop alalysis! But, nothing here :/")

    def _classifier_analysis(self):
        # TODO: Acresentar "trava" de último candle analisado
        self._analyze_for(self.Classifier)

    def _analyze_for(self, Analyzer):
        self.KlinesGetter.time_frame = Analyzer.parameters.time_frame

        Analyzer.data_to_analyze = self.KlinesGetter._get_n_until(
            number_of_candles=Analyzer.n_samples_to_analyze, until=self._now
        )

        self._hint_side = Analyzer.define_side()

    def run(self):
        self.operation.update(status=stat.Running)

        while self.operation.status == stat.Running:
            self._do_analysis()
            self._get_ready_to_repeat()

        # self._end()
