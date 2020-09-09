from ..settings import PossibleSides as Side, PossibleSignals as Sig


class Signal:

    def __init__(self, from_side: str, to_side: str, by_stop=False):
        self.from_side = from_side.capitalize()
        self.to_side = to_side.capitalize()
        self.by_stop = by_stop

    def get(self):
        if self.from_side == self.to_side:
            return Sig.Hold

        if self.from_side == Side.Zeroed:
            if self.to_side == Side.Long:
                return Sig.Buy

            if self.to_side == Side.Short:
                return Sig.NakedSell

        if self.from_side == Side.Long:
            if self.to_side == Side.Zeroed:
                if self.by_stop:
                    return Sig.StoppedFromLong
                return Sig.Sell

            if to_side == Side.Short:
                return Sig.DoubleNakedSell

        if self.from_side == Side.Short:
            if to_side == Side.Zeroed:
                if self.by_stop:
                    return Sig.StoppedFromShort
                return Sig.Buy

            if to_side == Side.Long:
                return Sig.DoubleNakedSell
