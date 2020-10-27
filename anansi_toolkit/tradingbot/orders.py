import json
from ..settings import (
    PossibleSignals as SIG,
    PossibleSides as SIDE,
    PossibleModes as MODE,
)
from ..share.tools import EventContainer, Serialize, table_from_dict
from ..share.brokers import instantiate_broker


class Order:
    def __init__(
        self,
        timestamp: int,
        from_side: str,
        to_side: str,
        price: float,
        due_to_stop: bool,
    ):
        self.timestamp = timestamp
        self.from_side = from_side
        self.to_side = to_side
        self.price = price
        self.due_to_stop = due_to_stop
        self.signal: str = SIG.Hold
        self.amount: float = None


class SignalGenerator:
    def __init__(self, allowed_special_signals):
        self.allowed_special_signals = allowed_special_signals
        self.signal = SIG.Hold
        self.side = SIDE.Zeroed

    def process(self, from_side: str, to_side: str, due_to_stop=False):
        self.side = to_side
        if from_side == to_side:
            self.signal = SIG.Hold

        if from_side == SIDE.Zeroed:
            if to_side == SIDE.Long:
                self.signal = SIG.Buy

            if to_side == SIDE.Short:
                if SIG.NakedSell in self.allowed_special_signals:
                    self.signal = SIG.NakedSell
                else:
                    self.signal = SIG.Hold
                    self.side = SIDE.Zeroed

        if from_side == SIDE.Long:
            if to_side == SIDE.Zeroed:
                if due_to_stop:
                    self.signal = SIG.StopFromLong
                self.signal = SIG.Sell

            if to_side == SIDE.Short:
                if SIG.DoubleSell in self.allowed_special_signals:
                    self.signal = SIG.DoubleSell
                else:
                    self.signal = SIG.Sell
                    self.side = SIDE.Zeroed

        if from_side == SIDE.Short:
            if to_side == SIDE.Zeroed:
                if due_to_stop:
                    self.signal = SIG.StopFromShort
                self.signal = SIG.Buy

            if to_side == SIDE.Long:
                if SIG.DoubleBuy in self.allowed_special_signals:
                    self.signal = SIG.DoubleBuy
                else:
                    self.signal = SIG.Buy
                    self.side = SIDE.Zeroed


class Handler:
    def __init__(self, operation, log):
        self.SigGen = SignalGenerator(operation.allowed_special_signals)
        self.op = operation
        self.log = log
        self._event = EventContainer(reporter=self.__class__.__name__)
        self.broker = instantiate_broker(operation.market.exchange)
        self.minimal_amount = self.broker.minimal_amount_for(
            self.op.market.ticker_symbol
        )
        self._order_execute = getattr(
            self, "_{}_executor".format((operation.mode).lower())
        )
        self._base = 0.0
        self._quote = 0.0
        self._trade_details = dict()

    def _report_to_log(self, event_description: str):
        self._event.description = event_description
        self.log.report(self._event)

    def _get_avaliable(self):
        self._base = self.op.position.assets.base
        self._quote = self.op.position.assets.quote

    def _calculate_amount(self):
        signal = self.SigGen.signal
        raw_amount = 0.0
        self._get_avaliable()

        if signal in [SIG.Buy, SIG.StopFromShort]:  # , SIG.DoubleBuy]:
            raw_amount = self._base / self.order.price

        elif signal in [SIG.Sell, SIG.StopFromLong]:  # , SIG.DoubleSell]:
            raw_amount = self._quote

        factor = int(raw_amount / self.minimal_amount)
        self.order.amount = factor * self.minimal_amount

    def _proceed_updates(self):
        self.op.position.assets.update(
            quote=self._new_quote_amount, base=self._new_base_amount
        )
        self.op.position.update(
            side=self.SigGen.side,
            traded_price=self.order.price,
            traded_at=self.order.timestamp,
            due_to_signal=self.order.signal,
        )
        self._trade_details = dict(
            timestamp=self.order.timestamp,
            signal=self.order.signal,
            price=self.order.price,
            quote_amount=self.order.amount,
            fee=self.fee_base,
        )
        self.op.new_trade_log(self._trade_details)

    def _notify_trade(self):
        if self.op.mode == MODE.BackTesting:
            print(table_from_dict(self._trade_details))

    def _backtesting_executor(self):
        signal = self.order.signal
        self.fee_quote = self.broker.fee_rate_decimal * self.order.amount
        self.fee_base = self.fee_quote * self.order.price

        if signal in [SIG.Buy, SIG.StopFromShort]:  # , SIG.DoubleBuy]:
            spent_base_amount = self.order.amount * self.order.price
            bought_quote_amount = self.order.amount - self.fee_quote
            self._new_quote_amount = self._quote + bought_quote_amount
            self._new_base_amount = self._base - spent_base_amount
            self._proceed_updates()

        elif signal in [SIG.Sell, SIG.StopFromLong]:  # , SIG.DoubleSell]:
            spent_quote_amount = self.order.amount
            bought_base_amount = (
                self.order.amount * self.order.price - self.fee_base
            )
            self._new_quote_amount = self._quote - spent_quote_amount
            self._new_base_amount = self._base + bought_base_amount
            self._proceed_updates()

    def execute(self, _order: dict):
        self.order = Order(**_order)
        self.SigGen.process(
            self.order.from_side, self.order.to_side, self.order.due_to_stop
        )
        self.order.signal = self.SigGen.signal
        if self.op.mode == MODE.Advisor:
            self._order_execute()

        else:
            if self.SigGen.signal not in [SIG.Hold, SIG.SkippedDueToStopLoss]:
                self._calculate_amount()
                funds = bool(self.order.amount > self.minimal_amount)

                if funds:
                    self._order_execute()

        # Here, the order goes to the log with the original 'to_side'
        # attribute (from trader), even if the 'side' attribute has
        # been adjusted by the 'SignalGenerator' due to a not allowed
        # signal. This is useful to check if the signal filtering is
        # working correctly.
        self.log.order = Serialize(self.order).to_dict()
        self._notify_trade()
