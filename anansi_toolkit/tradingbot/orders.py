from pony.orm import commit
import json
from ..settings import (
    PossibleSignals as SIG,
    PossibleSides as SIDE,
    PossibleModes as MODE,
)
from ..share.tools import EventContainer, Serialize
from .trade_brokers import trade_broker


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
        self.operation = operation
        self.log = log
        self._event = EventContainer(reporter=self.__class__.__name__)
        self.quote_key = operation.market.quote_asset_symbol
        self.base_key = operation.market.base_asset_symbol
        ticker_symbol = self.quote_key + self.base_key
        self.broker = trade_broker(operation.market.exchange, ticker_symbol)
        self._order_execute = getattr(
            self, "_{}_executor".format((operation.mode).lower())
        )

    def _report_to_log(self, event_description: str):
        self._event.description = event_description
        self.log.report(self._event)

    def _avaliable(self, asset: str):
        try:
            return json.loads(self.operation.position.current_assets)[asset]

        except Exception as e:
            msg = "Fail to get avaliable {} due to {}".format(asset, e)
            self._report_to_log(msg)
            return 0.0

    def _calculate_amount(self):
        signal = self.SigGen.signal
        raw_amount = 0.0

        if signal in [SIG.Buy, SIG.StopFromShort]:  # , SIG.DoubleBuy]:
            raw_amount = self._avaliable(self.base_key) / self.order.price

        elif signal in [SIG.Sell, SIG.StopFromLong]:  # , SIG.DoubleSell]:
            raw_amount = self._avaliable(self.quote_key)

        factor = int(raw_amount / self.broker.mininal_amount)
        self.order.amount = factor * self.broker.mininal_amount

    def _proceed_updates(self):
        new_assets = {
            self.quote_key: self._new_quote_amount,
            self.base_key: self._new_base_amount,
        }
        self.operation.position.update(
            side=self.SigGen.side,
            current_assets=json.dumps(new_assets),
            due_to_signal=self.order.signal,
        )
        kwargs = dict(
            timestamp=self.order.timestamp,
            signal=self.order.signal,
            price=self.order.price,
            fee=self.fee_base,
            quote_amount=self.order.amount,
        )
        self.operation.trades_log.create(**kwargs)
        commit()

    def _backtesting_executor(self):
        signal = self.order.signal
        self.fee_quote = self.broker.fee_rate_decimal * self.order.amount
        self.fee_base = self.fee_quote * self.order.price

        if signal in [SIG.Buy, SIG.StopFromShort]:  # , SIG.DoubleBuy]:
            spent_base_amount = self.order.amount * self.order.price
            bought_quote_amount = self.order.amount - self.fee_quote
            self._new_quote_amount = (
                self._avaliable(self.quote_key) + bought_quote_amount
            )
            self._new_base_amount = (
                self._avaliable(self.base_key) - spent_base_amount
            )
            self._proceed_updates()

        elif signal in [SIG.Sell, SIG.StopFromLong]:  # , SIG.DoubleSell]:
            spent_quote_amount = self.order.amount
            bought_base_amount = (
                self.order.amount * self.order.price - self.fee_base
            )
            self._new_quote_amount = (
                self._avaliable(self.quote_key) - spent_quote_amount
            )
            self._new_base_amount = (
                self._avaliable(self.base_key) + bought_base_amount
            )
            self._proceed_updates()

    def _advisor_executor(self):
        pass

    def execute(self, _order: dict):
        self.order = Order(**_order)
        self.SigGen.process(
            self.order.from_side, self.order.to_side, self.order.due_to_stop
        )
        self.order.signal = self.SigGen.signal
        if self.operation.mode == MODE.Advisor:
            self._order_execute()

        else:
            if self.SigGen.signal not in [SIG.Hold, SIG.SkippedDueToStopLoss]:
                self._calculate_amount()
                funds = bool(self.order.amount > self.broker.mininal_amount)

                if funds:
                    self._order_execute()

        # Here, the order goes to the log with the original 'to_side'
        # attribute (from trader), even if the 'side' attribute has
        # been adjusted by the 'SignalGenerator' due to a not allowed
        # signal. This is useful to check if the signal filtering is
        # working correctly.
        self.log.order = Serialize(self.order).to_dict()
