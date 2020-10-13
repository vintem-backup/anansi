from ..settings import Default, Environments, kline_desired_informations
from ..share.tools import DefaultPrintLog
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
    sql_debug,
)

db, env = Database(), Environments.ENV

db.bind(**env.ORM_bind_to)
sql_debug(env.SqlDebug)

# Common extension ('MixIn') for a several models
class AttributeUpdater(object):
    def update(self, **kwargs):
        for item in kwargs.items():
            setattr(self, item[0], item[1])
            commit()


# Database models
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
    side = Required(str, default=Default.side)
    initial_assets = Required(Json, default=json.dumps(Default.initial_assets))
    current_assets = Required(Json, default=json.dumps(Default.initial_assets))
    due_to_signal = Optional(str)
    exit_reference_price = Optional(float)


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
    quote_asset_symbol = Required(str, default=Default.quote_asset_symbol)
    base_asset_symbol = Required(str, default=Default.base_asset_symbol)


class LastCheck(db.Entity, AttributeUpdater):
    Operation = Optional(lambda: Operation)  # Foreing key
    by_classifier_at = Optional(int)  # UTC timestamp
    by_stop_loss_at = Optional(int)  # UTC timestamp


class Operation(db.Entity, AttributeUpdater):
    user = Required(User)  # Foreing key
    trader = Required(str, default=Default.trader)
    position = Required(Position, cascade_delete=True)
    market = Required(Market, cascade_delete=True)
    classifier = Required(Classifier, cascade_delete=True)
    stop_loss = Required(StopLoss, cascade_delete=True)

    mode = Required(str, default=Default.mode)
    is_stop_loss_enabled = Required(bool, default=False)
    allowed_special_signals = Required(
        StrArray, default=Default.allowed_special_signals
    )
    status = Required(str, default=Default.status)
    last_check = Required(LastCheck)
    operational_log = Set(lambda: OperationalLog, cascade_delete=False)
    trades_log = Set(lambda: TradeLog, cascade_delete=False)


class OperationalLog(db.Entity):
    # Present in all logs:
    operation = Optional(Operation)  # Foreing key
    timestamp = Optional(int)  # UTC
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
    fee = Optional(float)  # base_asset units
    quote_amount = Optional(float)  # no discount due to fees


db.generate_mapping(create_tables=True)



# Specific database models handlers


class DefaultLog(DefaultPrintLog):
    """ TODO: Testar injetar esta classe como MixIn em 'OperationLog'.
    TODO: Não mais herdar de 'DefaultPrintLog'. A incumbência de formarmatar
    e imprimir a mensagem de log deve ser do trader, que conhece o
    formato do dado.
    """
    log_dicts = [
        "last_analyzed_data",
        "analysis_result",
        "order",
        "events_on_a_cycle",
    ]

    def __init__(self, operation):
        self.operation = operation
        self.append_log_to_database = getattr(
            self, "_{}_log_append".format((operation.mode).lower())
        )
        self._reset()

    def _reset(self):
        self._timestamp = 0
        self.analyzed_by = ""
        for attribute_name in self.log_dicts:
            setattr(self, attribute_name, dict())

    def _log_dicts_to_json(self):
        for attribute_name in self.log_dicts:
            attribute = getattr(self, attribute_name)
            attribute_value = json.dumps(attribute)
            setattr(self, attribute_name, attribute_value)

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
