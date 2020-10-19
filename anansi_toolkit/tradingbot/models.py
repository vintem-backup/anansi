import json
import pendulum
from pony.orm import (
    Database,
    Json,
    Optional,
    Required,
    Set,
    StrArray,
    commit,
    rollback,
    sql_debug,
    TransactionError,
)
from ..settings import (
    Default,
    Environments,
    PossibleSides as SIDE,
)
from .mixins import Report

db, env = Database(), Environments.ENV

db.bind(**env.ORM_bind_to)
sql_debug(env.SqlDebug)


def _safety_commit(retry=15):
    attempts = 0
    while attempts < retry:
        attempts += 1
        try:
            commit()
            break
        except:  #!TODO: To logging
            continue
    if attempts >= retry:
        rollback()
    return


class AttributeUpdater(object):
    def update(self, **kwargs):
        for item in kwargs.items():
            setattr(self, item[0], item[1])
            _safety_commit()
        return


class User(db.Entity, AttributeUpdater):
    first_name = Required(str, unique=True)
    last_name = Optional(str)
    email = Optional(str)
    operations = Set(lambda: Operation, cascade_delete=True)

    @property
    def login_displayed_name(self):
        return "{}_{}".format(self.first_name, self.last_name)


class Position(db.Entity, AttributeUpdater):
    operation = Optional(lambda: Operation)  # Foreing key
    assets = Required(lambda: Assets, cascade_delete=True)
    side = Required(str, default=Default.side)
    traded_price = Optional(float)
    traded_at = Optional(int)  # UTC timestamp
    due_to_signal = Optional(str)
    exit_reference_price = Optional(float)


class Assets(db.Entity, AttributeUpdater):
    position = Optional(Position)
    quote = Optional(float, default=0.0)
    base = Optional(float, default=0.0)


class Classifier(db.Entity, AttributeUpdater):
    operation = Optional(lambda: Operation)  # Foreing key
    name = Required(str)
    parameters = Optional(Json)


class StopLoss(db.Entity, AttributeUpdater):
    operation = Optional(lambda: Operation)  # Foreing key
    name = Required(str)
    parameters = Optional(Json)


class Market(db.Entity):
    ## It is not advisable to make the attributes below editable.
    operation = Optional(lambda: Operation)  # Foreing key
    exchange = Required(str, default=Default.exchange)
    quote_symbol = Required(str, default=Default.quote_symbol)
    base_symbol = Required(str, default=Default.base_symbol)

    @property
    def ticker_symbol(self):
        return self.quote_symbol + self.base_symbol


class LastCheck(db.Entity, AttributeUpdater):
    Operation = Optional(lambda: Operation)  # Foreing key
    by_classifier_at = Optional(int)  # UTC timestamp
    by_stop_loss_at = Optional(int)  # UTC timestamp


class OperationMixIn:
    def _reset_assets(self):
        self.position.assets.update(quote=0.0, base=self.initial_base_amount)
        return

    def clear_logs(self):
        self.operational_log.clear()
        self.trades_log.clear()
        _safety_commit()
        return

    def if_no_assets_fill_them(self):
        no_assets = bool(
            self.position.assets.quote == 0.0
            and self.position.assets.base == 0.0
        )
        if no_assets:
            self._reset_assets()
        return

    def reset(self):
        self.last_check.update(by_classifier_at=0)
        self.position.update(side=SIDE.Zeroed)
        self._reset_assets()
        self.clear_logs()
        return

    def new_trade_log(self, trade_details: dict):
        self.trades_log.create(**trade_details)
        _safety_commit()
        return


class Operation(db.Entity, AttributeUpdater, OperationMixIn, Report):
    user = Required(User)  # Foreing key
    trader = Required(str, default=Default.trader)
    position = Required(Position, cascade_delete=True)
    market = Required(Market, cascade_delete=True)
    classifier = Required(Classifier, cascade_delete=True)
    stop_loss = Required(StopLoss, cascade_delete=True)
    initial_base_amount = Optional(float, default=Default.initial_base_amount)

    mode = Required(str, default=Default.mode)
    is_stop_loss_enabled = Required(bool, default=False)
    allowed_special_signals = Required(
        StrArray, default=Default.allowed_special_signals
    )
    status = Required(str, default=Default.status)
    last_check = Required(LastCheck)
    operational_log = Set(lambda: OperationalLog, cascade_delete=True)
    trades_log = Set(lambda: TradeLog, cascade_delete=True)


class OperationalLog(db.Entity):
    # Present in all logs:
    operation = Optional(Operation)  # Foreing key
    timestamp = Optional(int)  # UTC
    price = Optional(float)
    equivalent_base_amount = Optional(
        float
    )  # TODO: The OperationMixIn will do this (maybe.)
    # Optional for each log:
    analyzed_by = Optional(str)
    last_analyzed_data = Optional(Json)
    analysis_result = Optional(Json)
    order = Optional(Json)
    events = Optional(Json)


class TradeLog(db.Entity, AttributeUpdater):
    operation = Optional(Operation)  # Foreing key
    timestamp = Optional(int)  # UTC
    signal = Optional(str)
    price = Optional(float)
    quote_amount = Optional(float)  # no discount due to fees
    fee = Optional(float)  # base units


class DefaultLog:
    """TODO: Refactoring suggestion: Make the log 100% json ('noSQl'), thus
    having total freedom over what to append, for each mode, on each cycle.
    The json could be deserialized, in order to consume the information when
    they gona need to be computed and reported.
    """

    def __init__(self, operation):
        self.operation = operation
        self.append_log_to_database = getattr(
            self, "_{}_log_append".format((operation.mode).lower())
        )
        self._reset()
        self._price: float = None
        self._equivalent_base_amount: float = None

    @property
    def price(self):
        return self._price

    @price.setter
    def price(self, price_to_set):
        if price_to_set:
            if price_to_set > 0.0:
                self._price = price_to_set

    def _reset(self):
        self._timestamp = 0
        self.analyzed_by = ""
        self.last_analyzed_data = dict()
        self.analysis_result = dict()
        self.order = dict()
        self.events_on_a_cycle = dict()

    def _log_dicts_to_json(self):
        self.last_analyzed_data = json.dumps(self.last_analyzed_data)
        self.analysis_result = json.dumps(self.analysis_result)
        self.events_on_a_cycle = json.dumps(self.events_on_a_cycle)
        self.order = json.dumps(self.order)

    def _create_operational_log(self, **kwargs):
        self.operation.operational_log.create(
            **kwargs, timestamp=self._timestamp
        )
        commit()
        self._reset()

    def _backtesting_log_append(self):
        kwargs = dict(
            analyzed_by=self.analyzed_by,
            last_analyzed_data=self.last_analyzed_data,
            analysis_result=self.analysis_result,
            order=self.order,
            events=self.events_on_a_cycle,
        )
        self._create_operational_log(**kwargs)

    def _real_trading_log_append(self):
        pass

    def _real_time_test_log_append(self):
        pass

    def _advisor_log_append(self):
        pass

    def report(self, event):
        event_key = "{}_{}".format(
            str(event.reporter), str(pendulum.now().int_timestamp)
        )
        self.events_on_a_cycle = {
            **self.events_on_a_cycle,
            event_key: event.description,
        }

    def update(self, timestamp: int = None):
        self._timestamp = (
            pendulum.now().int_timestamp if not timestamp else timestamp
        )
        if env.print_log:
            self.print_log()

        self._log_dicts_to_json()
        self.append_log_to_database()
