import pendulum
import pandas as pd
from .order_handler import *
from . import classifiers, stop_handlers, order_handler
from ..marketdata import klines
from ..share.tools import ConvertTimeFrame
from ..settings import (PossibleSides as side,
                        PossibleStatuses as stat, PossibleModes as mode)


class Log:

    def __init__(self, operation):
        self.operation = operation
        self.analyzed_data = None
        self.analyzer = None
        self.current_side = None
        self.hint_side = None
        self.signal = None
        self.exit_price = None
        self.quote = None
        self.base = None

    def consolidate(self):
        """Cria um só dataframe (linha), com os atributos de interesse durante o
        ciclo + dados - OHLCV - (no caso de back testing).
        """

        self.log_dataframe = self.analyzed_data.assign(
            analyzer=self.analyzer,
            current_side=self.current_side,
            hint_side=self.hint_side,
            signal=self.signal,
            exit_price=self.exit_price,
            quote=self.quote,
            base=self.base)

        return self.log_dataframe

    def append_to_db(self):
        pass

    def get_from_db(self, number_of_lines):
        pass

    def show(self, number_of_lines):
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
        self.log = Log(operation=self.operation)

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
                   self.Classifier.NumberOfSamplesToAnalysis))

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
        print("Finally stop alalysis! But, nothing here :/")

    def _classifier_analysis(self):
        # TODO: Acresentar "trava" de último candle analisado
        self._analyze_for(self.Classifier)

    def _analyze_for(self, Analyzer):
        self.KlinesGetter.time_frame = Analyzer.parameters.time_frame

        Analyzer.data_to_analyze = self.KlinesGetter._get_n_until(
            number_of_candles=Analyzer.NumberOfSamplesToAnalysis,
            until=self._now)

        Analyzer.perform_analysis()

    def run(self):
        while self.operation.status == stat.Running:
            self._do_analysis()
            self._get_ready_to_repeat()

        # self._end()
