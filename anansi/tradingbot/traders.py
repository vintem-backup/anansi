import pendulum
from .models import Log
from . import classifiers, stop_handlers, order_handler
from ..marketdata.handlers import *
from ..share.tools import get_signal, seconds_in
from ..settings import (
    PossibleSides as Side,
    PossibleStatuses as stat,
    PossibleModes as mode,
    PossibleSignals as sig,
)


class DefaultTrader:
    def __init__(self, operation):
        ticker_symbol = (operation.market.quote_asset_symbol
                         + operation.market.base_asset_symbol)

        self._step = None
        self.operation = operation

        self.log = Log(operation)
        self.OrderHandler = (order_handler.OrderHandler(operation=operation,
                                                        log=self.log))

        self.Classifier = getattr(classifiers, operation.classifier.name)(
            parameters=operation.classifier.parameters, log=self.log)

        self._classifier_time_frame_in_seconds = seconds_in(
            self.Classifier.parameters.time_frame)

        self.StopLoss = getattr(stop_handlers, operation.stop_loss.name)(
            parameters=operation.stop_loss.parameters, log=self.log)

        self._stop_loss_time_frame_in_seconds = seconds_in(
            self.StopLoss.parameters.time_frame)

        self.Klines = (
            BackTestingKlines(operation.market.exchange, ticker_symbol)
            if operation.mode == mode.BackTesting
            else KlinesFromBroker(operation.market.exchange, ticker_symbol))

        self._now = (
            self._get_initial_backtesting_now()
            if self.operation.mode == mode.BackTesting
            else pendulum.now().int_timestamp)

        self.OrderHandler._now = self._now  # Important if BackTesting mode
        self._final_backtesting_now = self._get_final_backtesting_now()

    def _get_initial_backtesting_now(self):
        self.Klines.time_frame = self.Classifier.parameters.time_frame

        step_in_seconds = (self._classifier_time_frame_in_seconds *
                           self.Classifier.n_samples_to_analyze)

        return self.Klines._oldest_open_time() + step_in_seconds

    def _get_final_backtesting_now(self):
        self.Klines.time_frame = self.Classifier.parameters.time_frame
        return self.Klines._newest_open_time()

    def _get_ready_to_repeat(self):
        if self.operation.mode == mode.BackTesting:
            self._now += self._step
            self.OrderHandler._now = self._now  # Important if BackTesting mode

            if self._now > self._final_backtesting_now:
                self.operation.status = stat.NotRunning
        else:
            time.sleep(self._step)  # ! Some calculation is needed here yet
            self._now = pendulum.now().int_timestamp

    def _do_analysis(self):
        if ((self.operation.stop_on) and
                (self.operation.position.side != Side.Zeroed)):

            self._step = self._stop_loss_time_frame_in_seconds
            self._stop_analysis()

        else:
            self._step = self._classifier_time_frame_in_seconds

        self._classifier_analysis()

    def _stop_analysis(self):
        print("Finally stop alalysis! But, nothing here :/")

    def _classifier_analysis(self):
        LastAnalyzedLongerThanTimeFrame = bool(
            self._now >= (
                self.operation.last_check.by_classifier_at +
                self._classifier_time_frame_in_seconds)
        )

        if LastAnalyzedLongerThanTimeFrame:
            self._analyze_for(self.Classifier)
            self.operation.last_check.update(by_classifier_at=self._now)
            self.log.update()

        else:
            print("Passing classifier analysis, cause there is no new kline to analyze.")

    def _analyze_for(self, Analyzer):
        self.Klines.time_frame = Analyzer.parameters.time_frame

        Analyzer.data_to_analyze = self.Klines.get(
            number_of_candles=Analyzer.n_samples_to_analyze,
            until=self._now)

        signal = self._get_signal_for_(Analyzer.result())
        self.OrderHandler.execute(signal)

    def _start(self):
        self.operation.update(status=stat.Running)

        if self.operation.mode == mode.BackTesting:
            self.operation.last_check.update(by_classifier_at=0)
            self.operation.position.update(Side=Side.Zeroed)

    def _end(self):
        print("It's the end!")  # Not decided what do here yet

    def _get_signal_for_(self, result):
        HoldIfStopped = self.operation.hold_if_stopped  # ! Check if bool or int
        RecentlyStopped = bool(
            self.operation.position.due_to_signal
            in [sig.StoppedFromLong, sig.StoppedFromShort]
        )

        if HoldIfStopped and RecentlyStopped:
            print("Passing, cause recently stopped!")
            return sig.Hold

        else:
            signal = get_signal(
                from_side=self.operation.position.side,
                to_side=result.side,
                by_stop=result.by_stop)

            print(" ")
            print("Original_signal: ", signal)

            return (
                sig.Hold
                if signal == sig.NakedSell
                else sig.Sell
                if signal == sig.DoubleNakedSell
                else sig.Buy
                if signal == sig.DoubleBuy
                else signal)

    def run(self):
        self._start()
        while self.operation.status == stat.Running:
            self._do_analysis()
            self._get_ready_to_repeat()

        self._end()
