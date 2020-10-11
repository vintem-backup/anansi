import json
import math
from . import trade_brokers
from .models import Portfolio, TradesRegister
from ..marketdata.handlers import *
from ..settings import (PossibleSides as SIDE, PossibleModes as MODE,
                        PossibleSignals as SIG, PossibleOrderTypes as ORD)
from ..share.tools import Serialize, EventContainer


class Handler:
    def __init__(self, operation, log):
        self.quote_key = "{}".format(operation.market.quote_asset_symbol)
        self.base_key = "{}".format(operation.market.base_asset_symbol)
        ticker_symbol = self.quote_key + self.base_key

        self.operation = operation
        self.event = EventContainer(reporter=self.__class__.__name__)
        self.trades = TradesRegister(operation)
        self.log = log
        self.order = None
        self._new_quote_amount = None
        self._new_base_amount = None

        self.broker = getattr(
            trade_brokers, "{}OrderBroker".format(
                (operation.market.exchange).capitalize()))(ticker_symbol)

        self.Pricing = (
            BackTestingPriceGetter(operation.market.exchange, ticker_symbol)
            if operation.mode == MODE.BackTesting
            else PriceGetter(operation.market.exchange, ticker_symbol))

        self._execute = getattr(
            self, "_{}OrderExecutor".format(operation.mode))

        self._now = None

    def _avaliable(self, asset: str):
        try:
            return self.operation.user.portfolio.assets[asset]
        except:
            try:
                return(
                    json.loads(self.operation.user.portfolio.assets)[asset])

            except Exception as e:
                self.event.description = (
                    "Fail to get asset in portfolio due to {}".format(e))

                self.log.report(self.event)
                return 0.0

    def _refresh_price(self):
        price = self.Pricing.get(at=self._now)
        if not math.isnan(price):
            self.order.price = price

    def _calculate_amount(self):
        self._refresh_price()
        price = self.order.price
        signal = self.order.signal
        exposure_factor = self.operation.exposure_factor
        raw_amount = 0.0

        if signal in [SIG.Buy, SIG.StopFromShort, SIG.DoubleBuy]:
            raw_amount = (2*self._avaliable(self.base_key)/price
                          if signal == SIG.DoubleBuy
                          else self._avaliable(self.base_key)/price)

        elif signal in [SIG.Sell, SIG.StopFromLong, SIG.DoubleNakedSell]:
            raw_amount = (2*self._avaliable(self.quote_key)
                          if signal == SIG.DoubleNakedSell
                          else self._avaliable(self.quote_key))

        integer_factor = int(
            exposure_factor*raw_amount/self.broker.mininal_amount)

        self.order.amount = integer_factor*self.broker.mininal_amount

    def _proceed_updates(self):
        NewAssetsComposition = {
            self.quote_key: self._new_quote_amount,
            self.base_key: self._new_base_amount}

        self.operation.user.portfolio.update(
            assets=json.dumps(NewAssetsComposition))

        print("side: {}, size_by_quote: {}, due_to_signal: {}".format(
            self._to_side, self.order.amount, self.order.signal))

        self.operation.position.update(side=self._to_side,
                                       size_by_quote=self.order.amount,
                                       due_to_signal=self.order.signal)

        self.event.description = (
            "Trade due to signal {}".format(self.order.signal))

        self.log.report(self.event)

    def _BackTestingOrderExecutor(self):
        signal = self.order.signal
        fee_quoted = self.broker.fee_rate_decimal*self.order.amount
        fee_base = fee_quoted*self.order.price

        if signal in [SIG.Buy, SIG.StopFromShort, SIG.DoubleBuy]:
            self._to_side = self.order.to_side

            spent_base_amount = self.order.amount*self.order.price
            bought_quote_amount = self.order.amount - fee_quoted

            self._new_quote_amount = (
                self._avaliable(self.quote_key) + bought_quote_amount)

            self._new_base_amount = (
                self._avaliable(self.base_key) - spent_base_amount)

            self._proceed_updates()

        elif signal in [SIG.Sell, SIG.StopFromLong, SIG.DoubleNakedSell]:
            self._to_side = self.order.to_side

            spent_quote_amount = self.order.amount
            bought_base_amount = self.order.amount*self.order.price - fee_base

            self._new_quote_amount = (
                self._avaliable(self.quote_key) - spent_quote_amount)

            self._new_base_amount = (
                self._avaliable(self.base_key) + bought_base_amount)

            self._proceed_updates()

    def execute(self, order):
        if order.signal not in [SIG.Hold, SIG.StopByPassed]:
            self.log.order = Serialize(order).to_dict()
            self.order = order

            if order.order_type == ORD.Market:
                self._calculate_amount()

            EnoughFunds = bool(
                self.order.amount > self.broker.mininal_amount)

            if EnoughFunds:
                self._execute()
