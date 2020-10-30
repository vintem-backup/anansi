# pylint: skip-file
import json
from ..share.tools import ParseDateTime
from pony.orm import select, desc
from ..share.tools import table_from_dict


class Report:
    def _init(self):
        self.sub_h = "### Cycle information ###"
        self.pos_h = "> Position"
        self.dta_h = "> Last Analyzed Data"
        self.res_h = "> Analysis Result"
        self.ord_h = "> Order"
        self.err_h = "> Errors, exceptions, warnings"
        self._log = (
            select(log for log in self.operational_log)
            .order_by(lambda log: desc(log.timestamp))
            .first()
        )
        self._amount_now = (
            self.position.assets.quote * self._log.price
            + self.position.assets.base
        )
        self._msg = ""

    def _header(self):
        dt = ParseDateTime(
            self._log.timestamp
        ).from_timestamp_to_human_readable()
        return "{} {} {} | {}".format(
            self.market.exchange, self.market.ticker_symbol, self.mode, dt
        )

    def _handlers_table(self):
        _handlers = dict(
            Trader=self.trader,
            Classifier=self.classifier.name,
            StopLoss=self.stop_loss.name,
        )

        return table_from_dict(_handlers)

    def _gains(self):
        amount_initial = self.initial_base_amount
        cumulated_gain_percent = (
            (self._amount_now - amount_initial) / amount_initial
        ) * 100
        if self.position.side == "Zeroed":
            position_gain_percent = 0

        else:
            delta = self._log.price - self.position.traded_price
            position_gain = (
                delta
                if self.position.side == "Long"
                else -delta
                if self.position.side == "Sell"
                else 0.0
            )
            position_gain_percent = (
                position_gain / self.position.traded_price
            ) * 100

        return "Cumulated ({}%) <> Due to position ({}%)".format(
            round(cumulated_gain_percent, 2), round(position_gain_percent, 2)
        )

    def _summary(self):
        _msg = "{}:\t{}\n{}:\t{}\nPrice:\t{}"
        return _msg.format(
            self.market.quote_symbol,
            self.position.assets.quote,
            self.market.base_symbol,
            self.position.assets.base,
            self._log.price,
        )

    def _position_table(self):  
        if self.position.side == "Zeroed":
            position = dict(Side=self.position.side)
        
        else:
            position = dict(
                Side=self.position.side,
                TradedPrice=self.position.traded_price,
                TradedAt=ParseDateTime(
                    self.position.traded_at
                ).from_timestamp_to_human_readable(),
            )
        return table_from_dict(position)

    def _total_display(self):
        _msg = "{} equivalent total:\t{}"
        return _msg.format(self.market.base_symbol, self._amount_now)

    def _add_display(self, my_dict: dict, title: str):
        self._msg += "\n\n\n{}\n\n{}".format(title, table_from_dict(my_dict))
        return

    def _base_msg(self):
        _base_template = "\n\n{}\n\n{}\n\n{}\n\n{}\n\n{}\n\n{}\n\n{}\n\n{}"
        return _base_template.format(
            self._header(),
            self._gains(),
            self._total_display(),
            self._handlers_table(),
            self._summary(),
            self.sub_h,
            self.pos_h,
            self._position_table(),
        )

    def msg(self):
        self._init()
        self._msg = self._base_msg()
        _data = json.loads(self._log.last_analyzed_data)
        _result = json.loads(self._log.analysis_result)
        _order = json.loads(self._log.order)
        _warnings = json.loads(self._log.events)

        if _data:
            self._add_display(_data, title=self.dta_h)

        if _result:
            self._add_display(_result, title=self.res_h)

        if _order:
            self._add_display(_order, title=self.ord_h)

        if _warnings:
            self._add_display(_warnings, title=self.err_h)

        return self._msg

    def print_report(self):
        print(self.msg())
