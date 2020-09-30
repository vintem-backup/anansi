import pendulum
from .models import DefaultLog
from . import classifiers, stop_handlers, order_handler
from ..marketdata.handlers import *
from ..share.tools import *
from ..settings import (
    PossibleSides as SIDE,
    PossibleStatuses as STAT,
    PossibleModes as MODE,
    PossibleSignals as SIG,
    PossibleOrderTypes as ORD,
)


class Order:
    # def __init__(self):
    signal: str = SIG.Hold
    to_side: str = None
    order_type = ORD.Market
    amount: float = None
    price: float = None


class DefaultTrader:
    def __init__(self, operation):
        ticker_symbol = (operation.market.quote_asset_symbol
                         + operation.market.base_asset_symbol)

        self._step = None
        self.operation = operation
        self.event = EventContainer(reporter=self.__class__.__name__)
        self.log = DefaultLog(operation)
        self.result = None
        self.order = Order()
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

        self.Klines = KlinesFromBroker(
            operation.market.exchange, ticker_symbol)

        self._now = pendulum.now().int_timestamp

        if self.operation.mode == MODE.BackTesting:
            self.Klines = BackTestingKlines(
                operation.market.exchange, ticker_symbol)

            self._now = self._get_initial_backtesting_now()
            self._final_backtesting_now = self._get_final_backtesting_now()

        self.OrderHandler._now = self._now  # Important if BackTesting mode

    def _get_initial_backtesting_now(self):
        self.Klines.time_frame = self.Classifier.parameters.time_frame

        step_in_seconds = (self._classifier_time_frame_in_seconds *
                           self.Classifier.n_samples_to_analyze)

        return self.Klines._oldest_open_time() + step_in_seconds

    def _get_final_backtesting_now(self):
        self.Klines.time_frame = self.Classifier.parameters.time_frame
        return self.Klines._newest_open_time()

    def _get_ready_to_repeat(self):
        if self.operation.mode == MODE.BackTesting:
            self._now += self._step
            self.OrderHandler._now = self._now  # Important if BackTesting mode

            if self._now > self._final_backtesting_now:
                self.operation.status = STAT.NotRunning
        else:
            sleep_time = (self._step
                          - pendulum.from_timestamp(self._now).second)

            time.sleep(sleep_time)
            self._now = pendulum.now().int_timestamp

    def _do_analysis(self):
        self._step = self._classifier_time_frame_in_seconds
        CheckStop = self.operation.stop_is_on
        IsPositioned = bool(
            self.operation.position.side != SIDE.Zeroed)

        if IsPositioned and CheckStop:
            self._step = self._stop_loss_time_frame_in_seconds
            self._stop_analysis()

        self._classifier_analysis()

    def _stop_analysis(self):
        print("Entering on null stoploss")

    def _classifier_analysis(self):
        NewDataToAnalyze = bool(
            self._now >= (
                self.operation.last_check.by_classifier_at +
                self._classifier_time_frame_in_seconds))

        if NewDataToAnalyze:
            self._analyze_for(self.Classifier)
            self.operation.last_check.update(by_classifier_at=self._now)

        else:
            print("No new data do analyze")

    def _analyze_for(self, Analyzer):
        self.Klines.time_frame = Analyzer.parameters.time_frame

        Analyzer.data_to_analyze = self.Klines.get(
            number_of_candles=Analyzer.n_samples_to_analyze,
            until=self._now)

        self.result = Analyzer.get_result()

    def _start(self):
        self.operation.update(status=STAT.Running)

        if self.operation.mode == MODE.BackTesting:
            self.operation.last_check.update(by_classifier_at=0)
            self.operation.position.update(Side=SIDE.Zeroed)

    def _end(self):  # Not decided what do here yet
        self.event.description = "It's the end!"
        self.log.report(self.event)

    def _prepare_order(self):
        self.order.price = self.result.price

        signal = get_signal(
            from_side=self.operation.position.side,
            to_side=self.result.side,
            by_stop=self.result.by_stop)

        self.event.description = "Original signal: {}".format(signal)
        self.log.report(self.event)

        HoldIfRecentlyStopped = self.operation.hold_if_stopped

        if HoldIfRecentlyStopped:
            StoppedFromLong = bool(
                self.operation.position.due_to_signal == SIG.StopFromLong)

            StoppedFromShort = bool(
                self.operation.position.due_to_signal == SIG.StopFromShort)

            IgnoreSignalDueToStop = bool(
                (signal == SIG.Buy and StoppedFromLong) or
                (signal == SIG.Sell and StoppedFromShort))

            if IgnoreSignalDueToStop:
                signal = SIG.StopByPassed
                self.event.description = signal
                self.log.report(self.event)

        if signal == SIG.NakedSell:
            self.order.signal = SIG.Hold

        elif signal == SIG.DoubleNakedSell:
            self.order.signal = SIG.Sell

        elif signal == SIG.DoubleBuy:
            self.order.signal = SIG.Buy

        if self.order.signal == SIG.Buy:
            self.order.to_side = SIDE.Long

        if self.order.signal == SIG.Sell:
            self.order.to_side = SIDE.Zeroed

    def run(self):
        self._start()
        while self.operation.status == STAT.Running:
            # try:
            self._do_analysis()
            self._prepare_order()
            self.OrderHandler.execute(self.order)
            self._get_ready_to_repeat()

            # except Exception as e:
            #    self.event.description = str(e)
            #    self.log.report(self.event)

            self.log.update()
        self._end()
