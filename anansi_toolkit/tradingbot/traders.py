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

#!TODO: Testar instanciamento com atributos default/kwargs
class Order:
    def __init__(
        self,
        timestamp:int,
        from_side: str,
        to_side: str,
        price: float,
        order_type=ORD.Market,
        by_stop=False,
    ):
        self.timestamp = timestamp
        self.from_side = from_side
        self.to_side = to_side
        self.price = price
        self.order_type = order_type
        self.by_stop = by_stop


class SimpleKlinesTrader:
    def __init__(self, operation):
        self.ticker_symbol = (
            operation.market.quote_asset_symbol
            + operation.market.base_asset_symbol
        )
        self.operation = operation
        self.event = tools.EventContainer(reporter=self.__class__.__name__)
        self.log = DefaultLog(operation)
        self.result = None
        self._step = None
        self.OrderHandler = orders.Handler(self.operation, self.log)
        self.Classifier = getattr(classifiers, operation.classifier.name)(
            parameters=operation.classifier.parameters, log=self.log
        )
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
        return self.KlinesGetter._oldest_open_time() + step_in_seconds

    def _get_final_backtesting_now(self):
        return self.KlinesGetter._newest_open_time()

    def _start(self):
        self._now = pendulum.now().int_timestamp
        self.operation.update(status=STAT.Running)

        if self.operation.mode == MODE.BackTesting:
            self.operation.last_check.update(by_classifier_at=0)
            self.operation.position.update(Side=SIDE.Zeroed)
            self._now = self._get_initial_backtesting_now()
            self._final_backtesting_now = self._get_final_backtesting_now()

    def _get_ready_to_repeat(self):
        if self.operation.mode == MODE.BackTesting:
            self._now += self._step

            if self._now > self._final_backtesting_now:
                self.operation.update(status=STAT.NotRunning)

        else:
            sleep_time = (
                self._step
                - pendulum.from_timestamp(self._now).second
            )
            time.sleep(sleep_time)
            self._now = pendulum.now().int_timestamp

    def _end(self):  # Not decided what do here yet
        self.event.description = "It's the end!"
        self.log.report(self.event)

    def _do_analysis(self):
        self._step = self.Classifier.step
        must_check_stop = self.operation.stop_is_on
        is_positioned = bool(self.operation.position.side != SIDE.Zeroed)

        if is_positioned and must_check_stop:
            pass
            # self._step = self.StopLoss.step
            # self._stop_analysis()

        self._classifier_analysis()

    def _stop_analysis(self):
        pass

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
            self.result = self.Classifier.get_result_for_this(data)
            self.operation.last_check.update(by_classifier_at=self._now)

    def _movement_moderator(self, current_side, suggested_side):
        return (current_side, suggested_side)

    #!TODO: order to log
    def _execute_the_order_if_the_side_changes(self):
        current_side, suggested_side = (
            self.operation.position.side,
            self.result.side,
        )
        if current_side != suggested_side:
            timestamp = self._now
            from_side, to_side = self._movement_moderator(
                current_side, suggested_side
            )
            price = self.PriceGetter.get(at=self._now)
            by_stop = self.result.by_stop
            order = Order(timestamp, from_side, to_side, price, by_stop)
            self.OrderHandler.execute(order)

    def run(self):
        self._start()
        while self.operation.status == STAT.Running:
            try:
                self._do_analysis()
                self._execute_the_order_if_the_side_changes()
                self._get_ready_to_repeat()

            except Exception as e:
                self.event.description = str(e)
                self.log.report(self.event)

            self.log.update()
        self._end()
