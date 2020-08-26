class CustomerMixin:
    pass


class PositionMixin:
    pass


class TraderMixin:
    pass


# class BkpTrader:
#    def __init__(self, market=Default.market, classifier=Default.classifier,
#                 stop_loss=Default.stop_loss, mode=Default.mode):
#        self.market = market
#        self.classifier = classifier
#        self.stop_loss = stop_loss
#        self.mode = mode

#    def convert_time_frame(self, tf):  # Just an example
#        return tools.ConvertTimeFrame(tf).to_seconds()
