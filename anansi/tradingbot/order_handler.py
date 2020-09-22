from . import trade_brokers
from .models import Wallet, TradesRegister
from ..settings import (
    PossibleSides as side,
    PossibleModes as mode,
    PossibleSignals as sig,
)

from ..marketdata import klines


class Signal:

    def __init__(self, from_side: str, to_side: str, by_stop=False):
        self.from_side = from_side.capitalize()
        self.to_side = to_side.capitalize()
        self.by_stop = by_stop

    def get(self):
        if self.from_side == self.to_side:
            return sig.Hold

        if self.from_side == side.Zeroed:
            if self.to_side == side.Long:
                return sig.Buy

            if self.to_side == side.Short:
                return sig.NakedSell

        if self.from_side == side.Long:
            if self.to_side == side.Zeroed:
                if self.by_stop:
                    return sig.StoppedFromLong
                return sig.Sell

            if to_side == side.Short:
                return sig.DoubleNakedSell

        if self.from_side == side.Short:
            if to_side == side.Zeroed:
                if self.by_stop:
                    return sig.StoppedFromShort
                return sig.Buy

            if to_side == side.Long:
                return sig.DoubleBuy


class OrderHandler:
    def __init__(self, operation):
        self._now = None
        self.operation = operation
        self.trades = TradesRegister(operation=self.operation)
        self.wallet = operation.user.wallet.assets
        self.signal = None
        self.quote_asset_amount = None
        self.price = None
        self.broker = getattr(trade_brokers, self.operation.market.exchange)(
            ticker_symbol=(
                self.operation.market.quote_asset_symbol
                + self.operation.market.base_asset_symbol))

    def _price(self):
        raise NotImplementedError

    def _amount(self):
        exposure_factor = self.operation.exposure_factor
        raw_quote_asset_amount = 0.0

        if self.signal == sig.Buy:
            try:
                avaliable_in_wallet = self.wallet[
                    self.operation.market.base_asset_symbol]

                raw_quote_asset_amount = (
                    exposure_factor*(avaliable_in_wallet/self._price()))
            except Exception as e:
                pass

        if self.signal == sig.Sell:
            try:
                avaliable_in_wallet = self.wallet[
                    self.operation.market.quote_asset_symbol]

                raw_quote_asset_amount = exposure_factor*(avaliable_in_wallet)
            except Exception as e:
                pass

        integer_factor = int(
            raw_quote_asset_amount/self.broker.mininal_amount())

        self.quote_asset_amount = integer_factor*self.broker.mininal_amount()
        return self.quote_asset_amount

    def execute(self, signal):
        if signal != sig.Hold:
            self.signal = signal

            if self._amount() > self.broker.mininal_amount():
                self._execute()

                print("Executed because {} > {}".format(
                    self.quote_asset_amount, self.broker.mininal_amount()))
                print(" ")

            else:
                print("Fail because {} < {}".format(
                    self.quote_asset_amount, self.broker.mininal_amount()))
                print(" ")

        else:
            print("Passing, signal = 'Hold'")


class BackTestingOrder(OrderHandler):
    def __init__(self, operation):
        self.KlinesGetter = klines.FromBroker(  # Por hora, evocando da corretora
            broker_name=operation.market.exchange,
            symbol=(
                operation.market.quote_asset_symbol
                + operation.market.base_asset_symbol))
        super(BackTestingOrder, self).__init__(operation)

    def _price(self):
        self.KlinesGetter.time_frame = "1m"
        last_kline = (self.KlinesGetter._get_n_until(
            number_of_candles=1, until=self._now))

        price = last_kline.apply_indicator.price._given(
            price_source="ohlc4")

        self.price = price.last()
        return self.price

    def _execute(self):
        print("Interpreted_signal: {}, price: {}".format(self.signal, self.price))
        print(" ")
