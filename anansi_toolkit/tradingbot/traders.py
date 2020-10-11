import time
import pendulum
from ..marketdata import handlers
from ..share import tools
from . import classifiers, orders
from .models import DefaultLog

from ..settings import (
    PossibleModes as MODE,
    PossibleOrderTypes as ORD,
    PossibleSides as SIDE,
    PossibleStatuses as STAT,
)


class Order:
    from_side: str = None
    to_side: str = None
    order_type = ORD.Market
    price: float = None


class KlinesSimpleTrader:
    def __init__(self, operation):
        self.ticker_symbol = (
            operation.market.quote_asset_symbol
            + operation.market.base_asset_symbol
        )
        self.operation = operation
        self.event = tools.EventContainer(reporter=self.__class__.__name__)
        self.log = DefaultLog(operation)
        self.result = None
        self.order = Order()
        self._intantiate_klines_getter()
        self.OrderHandler = orders.Handler(self.operation, self.log)
        self.Classifier = getattr(classifiers, operation.classifier.name)(
            parameters=operation.classifier.parameters, log=self.log
        )

    def _intantiate_klines_getter(self):
        mode = self.operation.mode
        kwargs = dict(
            broker_name=self.operation.market.exchange,
            ticker_symbol=self.ticker_symbol,
        )

        self.KlinesGetter = (
            handlers.BackTestingKlines(**kwargs)
            if mode == MODE.BackTesting
            else handlers.KlinesFromBroker(**kwargs)
        )

    def _get_initial_backtesting_now(self):
        self.KlinesGetter.time_frame = self.Classifier.parameters.time_frame

        step_in_seconds = (
            self.Classifier.step * self.Classifier.number_of_candles
        )

        return self.KlinesGetter._oldest_open_time() + step_in_seconds

    def _get_final_backtesting_now(self):
        self.KlinesGetter.time_frame = self.Classifier.parameters.time_frame
        return self.KlinesGetter._newest_open_time()

    def _get_ready_to_repeat(self):
        if self.operation.mode == MODE.BackTesting:
            self._now += self.Classifier.step

            if self._now > self._final_backtesting_now:
                self.operation.status = STAT.NotRunning
        
        else:
            sleep_time = self._step - pendulum.from_timestamp(self._now).second
            time.sleep(sleep_time)
            self._now = pendulum.now().int_timestamp

    def _do_analysis(self):
        self._classifier_analysis()


    def _classifier_analysis(self):
        NewDataToAnalyze = bool(
            self._now
            >= (
                self.operation.last_check.by_classifier_at
                + self.Classifier.step
            )
        )

        if NewDataToAnalyze:
            self._analyze_for(self.Classifier)
            self.operation.last_check.update(by_classifier_at=self._now)

        else:
            print("No new data do analyze")

    def _analyze_for(self, Analyzer):
        self.KlinesGetter.time_frame = Analyzer.parameters.time_frame

        data = self.KlinesGetter.get(
            number_of_candles=Analyzer.number_of_candles, until=self._now
        )

        self.result = Analyzer.get_result_for_this(data)

    def _start(self):
        self._now = pendulum.now().int_timestamp
        self.operation.update(status=STAT.Running)

        if self.operation.mode == MODE.BackTesting:
            self.operation.last_check.update(by_classifier_at=0)
            self.operation.position.update(Side=SIDE.Zeroed)
            self._now = self._get_initial_backtesting_now()
            self._final_backtesting_now = self._get_final_backtesting_now()

    def _end(self):  # Not decided what do here yet
        self.event.description = "It's the end!"
        self.log.report(self.event)

    def _prepare_order(self):
        self.order.price = 9000.0  #! Just a mock



    def run(self):
        self._start()
        while self.operation.status == STAT.Running:
            try:
                self._do_analysis()
                self._prepare_order()
                self.OrderHandler.execute(self.order)
                self._get_ready_to_repeat()

            except Exception as e:
                self.event.description = str(e)
                self.log.report(self.event)

            self.log.update()
        self._end()
