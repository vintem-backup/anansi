from . import trade_brokers
from .models import Wallet, TradesRegister
from ..settings import (
    PossibleSides as side,
    PossibleModes as mode,
    PossibleSignals as sig,
)


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
        self.operation = operation
        self.trades = TradesRegister(operation=self.operation)
        wallet = Wallet(user=self.operation.user)
        self.signal = None
        self.amount = None
        executor = "_{}_executor".format(self.operation.mode)
        self._execute = getattr(self, executor)
        self.broker = getattr(trade_brokers, self.operation.market.exchange)(
            ticker_symbol=(
                self.operation.market.quote_asset_symbol
                + self.operation.market.base_asset_symbol))

    def _price(self):
        pass

    def _amount(self):
        factor = self.operation.exposure_factor

        amount = factor*100.0

        self.amount = amount

        return amount

    def _save_movement(self):
        pass

    def _update_position(self):
        pass

    def _update_wallet(self):
        pass

    def _RealTrading_executor(self):
        pass

    def _RealTimeTest_executor(self):
        pass

    def _BackTesting_executor(self):

        print("Interpreted_signal: ", self.signal)
        print(" ")

    def execute(self, signal):
        self.signal = signal

        if self._amount() > self.broker.mininal_amount():
            self._execute()

            print("Executed because {} > {}".format(
                self.amount, self.broker.mininal_amount()))
            print(" ")

        else:
            print("Fail because {} < {}".format(
                self.amount, self.broker.mininal_amount()))
            print(" ")
