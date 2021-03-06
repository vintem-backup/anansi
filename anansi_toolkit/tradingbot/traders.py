import time
import pendulum
import math
from ..marketdata import handlers
from ..share.tools import EventContainer
from . import classifiers, orders
from .models import DefaultLog

from ..settings import (
    PossibleModes as MODE,
    PossibleOrderTypes as ORD,
    PossibleSides as SIDE,
    PossibleStatuses as STAT,
)

class SimpleKlinesTrader:
    def __init__(self, operation):
        self._event = EventContainer(reporter=self.__class__.__name__)
        self.ticker_symbol = (
            operation.market.quote_symbol + operation.market.base_symbol
        )
        self.log = DefaultLog(operation)
        self.OrderHandler = orders.Handler(operation, self.log)
        self.Classifier = getattr(classifiers, operation.classifier.name)(
            parameters=operation.classifier.parameters, log=self.log
        )
        self.operation = operation
        self.last_result = None
        self._step:int = None
        self._price_now:float = None
        self._instantiate_klines_and_price_getters()

    def _instantiate_klines_and_price_getters(self):
        backtesting = bool(self.operation.mode == MODE.BackTesting)
        kwargs = dict(
            broker_name=self.operation.market.exchange,
            ticker_symbol=self.ticker_symbol,
        )
        tf = dict(time_frame=self.Classifier.parameters.time_frame)
        self.KlinesGetter = (
            handlers.BackTestingKlines(**kwargs, **tf)
            if backtesting
            else handlers.KlinesFromBroker(**kwargs, **tf)
        )
        self.PriceGetter = (
            handlers.BackTestingPriceGetter(**kwargs)
            if backtesting
            else handlers.PriceGetter(**kwargs)
        )

    def _get_initial_backtesting_now(self):
        step_in_seconds = (
            self.Classifier.step * self.Classifier.number_of_candles
        )
        return self.KlinesGetter._oldest_open_time() + step_in_seconds + 3

    def _get_final_backtesting_now(self):
        return self.KlinesGetter._newest_open_time()

    def _start(self):  
        self.operation.if_no_assets_fill_them() 
        self._now = pendulum.now().int_timestamp
        self.operation.update(status=STAT.Running)

        if self.operation.mode == MODE.BackTesting:
            self.operation.reset()
            
            #TODO: Refactoring suggestion: The initial and final 
            # values ??????of '_now' must be attributes of the operation
            self._now = self._get_initial_backtesting_now()
            self._final_backtesting_now = self._get_final_backtesting_now()

    def _get_ready_to_repeat(self):
        self._consolidate_log()
        if self.operation.mode == MODE.BackTesting:
            self.operation.print_report()
            self._now += self._step

            if self._now > self._final_backtesting_now:
                self.operation.update(status=STAT.NotRunning)

        else:
            sleep_time = (
                self._step
                - pendulum.from_timestamp(self._now).second
            )
            time.sleep(sleep_time)
            self._now = pendulum.now().int_timestamp + 3

    def _end(self):  #TODO: Make a final report
        self._report_to_log("It's the end!") #TODO: Not appending, cause is after "repeat"

    def _get_price(self):
        price = self.PriceGetter.get(at=self._now)
        if math.isnan(price):
            raise ValueError("Fail to get price")
        else:
            self._price_now = price
        return

    def _do_analysis(self):
        self._get_price()
        self._step = self.Classifier.step
        is_positioned = bool(self.operation.position.side != SIDE.Zeroed)

        if is_positioned and self.operation.is_stop_loss_enabled:
            pass
            # self._step = self.StopLoss.step
            # self._stop_analysis()

        self._classifier_analysis()

    def _classifier_analysis(self):
        is_there_a_new_candle = bool(
            self._now
            >= (
                self.operation.last_check.by_classifier_at
                + self.Classifier.step
            )
        )
        if is_there_a_new_candle:
            kwargs = dict(
                number_of_candles=self.Classifier.number_of_candles,
                until=self._now,
            )
            data = self.KlinesGetter.get(**kwargs)
            self.last_result = self.Classifier.get_result_for_this(data)
            self.operation.last_check.update(by_classifier_at=self._now)
    
    def _stop_analysis(self):
        pass

    def _execute_the_order_if_the_side_changes(self):
        current_side = self.operation.position.side
        suggested_side = self.last_result.side
        
        if current_side != suggested_side:
            order = dict(
                timestamp=self._now,
                from_side=current_side,
                to_side=suggested_side, 
                price = self._price_now,
                due_to_stop = self.last_result.due_to_stop,
            )
            self.OrderHandler.execute(order)

    def _report_to_log(self, event_description:str):
        self._event.description = event_description
        self.log.report(self._event)

    def _consolidate_log(self):
        self.log.price = self._price_now
        self.log.update(timestamp=self._now)
        return
    
    def run(self):
        self._start()
        while self.operation.status == STAT.Running:
            try:
                self._do_analysis()
                self._execute_the_order_if_the_side_changes()
            except (Exception, ConnectionError) as e:
                self._report_to_log(str(e))
            
            self._get_ready_to_repeat()
        self._end()
