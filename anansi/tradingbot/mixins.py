from marketdata import klines


class CustomerMixin(object):
    def get_name(self):
        return "{}".format(self.user_name)


class PositionMixin:
    pass


class TraderMixin:

    def _init(self):
        self.Classifier = getattr(
            classifiers, self.classifier_name)(
                self.classifier_parameters)

        if self.mode == "BackTesting":
            # self._now =
            self.KStreamer = klines.FromBroker(
                broker_name=self.exchange, symbol=self.symbol)

    def _do_analysis(self):
        positioned = bool(self.position.side != "zeroed")
        if not self.by_pass_stop:
            if positioned:
                self.stop_analysis()
        self.classifier_analysis()

    def _analysis_pipeline(self, Analyzer):
        self.KStreamer.time_frame = self.Analyzer.parameters.time_frame
        self.Analyzer.klines = KStreamer.newest(
            number_of_candles=Analyzer.how_many_candles()
        )
        self.Analyzer.proceed_analysis()

    def classifier_analysis(self):
        self._analysis_pipeline(Classifier)

    def stop_analysis(self):
        self._analysis_pipeline(self.StopLoss)

    def _step_forward_cycle(self):
        pass

    def _end(self):
        pass

    def run(self):
        self._init()
        while self.status == "Running":
            self._do_analysis()
            self._step_forward_cycle()

        self._end()
