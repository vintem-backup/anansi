from ..settings import PossibleSides as side, PossibleSignals as Sig


class Signal:

    def __init__(self, from_side: str, to_side: str, by_stop=False):
        self.from_side = from_side.capitalize()
        self.to_side = to_side.capitalize()
        self.by_stop = by_stop

    def get(self):
        if self.from_side == self.to_side:
            return Sig.Hold

        if self.from_side == side.Zeroed:
            if self.to_side == side.Long:
                return Sig.Buy

            if self.to_side == side.Short:
                return Sig.NakedSell

        if self.from_side == side.Long:
            if self.to_side == side.Zeroed:
                if self.by_stop:
                    return Sig.StoppedFromLong
                return Sig.Sell

            if to_side == side.Short:
                return Sig.DoubleNakedSell

        if self.from_side == side.Short:
            if to_side == side.Zeroed:
                if self.by_stop:
                    return Sig.StoppedFromShort
                return Sig.Buy

            if to_side == side.Long:
                return Sig.DoubleNakedSell


class OrderHandler:
    def __init__(self, operation):
        self.operation = operation
