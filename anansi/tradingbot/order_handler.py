from . import trade_brokers
from .models import Portfolio, TradesRegister
from ..marketdata.handlers import BackTestingPriceGetter
from ..settings import PossibleSignals as sig  # PossibleSides as Side,


class OrderHandler:
    def __init__(self, operation, log):
        self._now = None
        self.operation = operation
        self.trades = TradesRegister(operation=self.operation)
        self.portfolio = operation.user.portfolio.assets
        self.signal = None
        self.quote_asset_amount = None
        self.price = None
        self.broker = getattr(trade_brokers, self.operation.market.exchange)(
            ticker_symbol=(
                self.operation.market.quote_asset_symbol
                + self.operation.market.base_asset_symbol))

        self.Pricing = BackTestingPriceGetter(
            broker_name=operation.market.exchange,
            ticker_symbol=(
                operation.market.quote_asset_symbol
                + operation.market.base_asset_symbol))

    # def _price(self):
    #    raise NotImplementedError

    def _price(self):
        self.price = self.Pricing.get(at=self._now)
        return self.price

    def _avaliable(self, _class: str):
        asset = getattr(
            self.operation.market, "{}_asset_symbol".format(_class))

        try:
            return self.portfolio[asset]

        except Exception as e:
            print("Fail get_in_portfolio due", e)
            return 0.0

    def _amount(self):
        exposure_factor = self.operation.exposure_factor

        raw_quote_asset_amount = (
            (self._avaliable("base")/self._price()) * exposure_factor
            if self.signal == sig.Buy
            else self._avaliable("quote") * exposure_factor
            if self.signal == sig.Sell
            else 0.0)

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

    def _execute(self):
        print("Interpreted_signal: {}, price: {}".format(self.signal, self.price))
        print(" ")


class BackTestingOrder(OrderHandler):
    def __init__(self, operation, log):

        self.Pricing = BackTestingPriceGetter(
            broker_name=operation.market.exchange,
            ticker_symbol=(
                operation.market.quote_asset_symbol
                + operation.market.base_asset_symbol))

        super(BackTestingOrder, self).__init__()

    def _price(self):
        self.price = self.Pricing.for_back_testing(at=self._now)
        return self.price

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

    def _execute(self):
        print("Interpreted_signal: {}, price: {}".format(self.signal, self.price))
        print(" ")
