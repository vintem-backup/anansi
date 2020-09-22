import pendulum
from .models import Logger
from . import classifiers, stop_handlers, order_handler
from ..marketdata import klines
from ..share.tools import seconds_in
from ..settings import (
    PossibleSides as side,
    PossibleStatuses as stat,
    PossibleModes as mode,
    PossibleSignals as sig,
)


class DefaultTrader:
    def __init__(self, operation):
        self.operation = operation
        self.logger = Logger(operation=self.operation)
        self._step = None
        self._by_stop = None
        self._signal = None

        self.Classifier = getattr(classifiers, self.operation.classifier.name)(
            parameters=self.operation.classifier.parameters
        )

        self._classifier_time_frame_in_seconds = seconds_in(
            self.Classifier.parameters.time_frame
        )

        self.StopLoss = getattr(stop_handlers, self.operation.stop_loss.name)(
            parameters=self.operation.stop_loss.parameters
        )

        self._stop_loss_time_frame_in_seconds = seconds_in(
            self.StopLoss.parameters.time_frame
        )

        self.KlinesGetter = klines.FromBroker(  # Por hora, evocando da corretora
            broker_name=self.operation.market.exchange,
            symbol=(
                self.operation.market.quote_asset_symbol
                + self.operation.market.base_asset_symbol
            ),
        )

        self.OrderHandler = getattr(order_handler,
                                    "{}Order".format(self.operation.mode))(
            operation=self.operation)

        self._now = (
            self._initial_now_for_backtesting()
            if self.operation.mode == mode.BackTesting
            else pendulum.now().int_timestamp
        )

        self.OrderHandler._now = self._now

    def _initial_now_for_backtesting(self):
        self.KlinesGetter.time_frame = self.Classifier.parameters.time_frame

        return self.KlinesGetter._oldest_open_time() + (
            self._classifier_time_frame_in_seconds
            * self.Classifier.n_samples_to_analyze
        )

    def _get_ready_to_repeat(self):
        if self.operation.mode == mode.BackTesting:
            self._now += self._step
            self.OrderHandler._now = self._now

            #! When the backtesting klines start to be produced
            #! synthetically from the database, this parameter must be the
            #! Open_time of the last available candle.
            if self._now > pendulum.now().int_timestamp:
                self.operation.status = stat.NotRunning
        else:
            time.sleep(self._step)
            self._now = pendulum.now().int_timestamp

    def _do_analysis(self):
        if (self.operation.stop_on) and (self.operation.position.side != side.Zeroed):

            self._step = self._stop_loss_time_frame_in_seconds
            self._stop_analysis()

        else:
            self._step = self._classifier_time_frame_in_seconds

        self._classifier_analysis()

    def _stop_analysis(self):
        self._by_stop = True
        print("Finally stop alalysis! But, nothing here :/")

    def _classifier_analysis(self):
        if self._now >= (
            self.operation.last_check.at + self._classifier_time_frame_in_seconds
        ):

            self._by_stop = False
            self._analyze_for(self.Classifier)

            self.logger.results_from = "CLASSIFIER ({})".format(
                self.operation.classifier.name
            )

            self.operation.last_check.update(by="classifier")
            self.logger.consolidate_log()

        else:
            print("Passing classifier analysis, cause there is no new candle.")

    def _analyze_for(self, Analyzer):
        self.operation.last_check.update(at=self._now)
        self.KlinesGetter.time_frame = Analyzer.parameters.time_frame

        Analyzer.data_to_analyze = self.KlinesGetter._get_n_until(
            number_of_candles=Analyzer.n_samples_to_analyze, until=self._now
        )

        self.logger.last_analyzed_data = Analyzer.data_to_analyze[-1:]
        self.logger.analysis_result = self.analysis_result = Analyzer.result()
        self._signal_interpreter()
        self.OrderHandler.execute(self._signal)

    def _start(self):
        self.operation.update(status=stat.Running)

        if self.operation.mode == mode.BackTesting:
            self.operation.last_check.update(at=0)
            self.operation.position.update(side=side.Zeroed)

    def _end(self):
        print("It's the end!")

    def _signal_interpreter(self):
        signal = order_handler.Signal(
            from_side=self.operation.position.side,
            to_side=self.analysis_result["Hint_side"],
            by_stop=self._by_stop,
        ).get()

        if self.operation.hold_if_stopped and (
            self.operation.position.due_the_signal
            in [sig.StoppedFromLong, sig.StoppedFromShort]
        ):

            self._signal = sig.Hold
            print("Passing, cause recently stopped!")

        else:
            self._signal = (
                sig.Hold
                if signal == sig.NakedSell
                else sig.Sell
                if signal == sig.DoubleNakedSell
                else sig.Buy
                if signal == sig.DoubleBuy
                else signal
            )

        print(" ")
        print("Original_signal: ", signal)

    def run(self):
        self._start()
        while self.operation.status == stat.Running:
            self._do_analysis()
            self._get_ready_to_repeat()

        self._end()
