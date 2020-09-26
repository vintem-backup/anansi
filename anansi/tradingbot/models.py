# import pandas as pd
import json
import pendulum
from pony.orm import *
from ..settings import *  # Default, Environments
from ..share.tools import PrintLog
from ..share.db_handlers import Storage

db, env = Database(), Environments.ENV

db.bind(**env.ORM_bind_to)
sql_debug(env.SqlDebug)


class AttributeUpdater(object):
    def update(self, **kwargs):
        for item in kwargs.items():
            setattr(self, item[0], item[1])
            commit()


class User(db.Entity, AttributeUpdater):
    first_name = Required(str, unique=True)
    last_name = Optional(str)
    email = Optional(str)
    operations = Set(lambda: Operation, cascade_delete=True)
    portfolio = Required(lambda: Portfolio, cascade_delete=True)
    trades_log = Set(lambda: TradeLog, cascade_delete=False)

    @property
    def login_displayed_name(self):
        return "{}_{}".format(self.first_name, self.last_name)


class Portfolio(db.Entity, AttributeUpdater):
    user = Optional(User)  # Foreing key
    assets = Optional(Json)


class Position(db.Entity, AttributeUpdater):
    operation = Optional(lambda: Operation)  # Foreing key
    side = Required(str, default=Default.side)
    size_by_quote = Optional(float)
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


class Market(db.Entity):  # I's not advise make attributes editable.
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
    # Leverage or portfolio proportion:
    exposure_factor = Required(float, default=1.0)
    classifier = Required(Classifier, cascade_delete=True)
    stop_loss = Required(StopLoss, cascade_delete=True)
    logs = Set(lambda: OperationLog)

    status = Required(str, default=Default.status)
    mode = Required(str, default=Default.mode)
    stop_on = Required(bool, default=True)
    hold_if_stopped = Required(bool, default=True)

    last_check = Required(LastCheck)


class OperationLog(db.Entity, AttributeUpdater):
    operation = Optional(Operation)  # Foreing key
    claimed_at = Optional(int)  # UTC timestamp
    analyzed_by = Optional(str)
    last_analyzed_data = Optional(FloatArray)
    analysis_result = Optional(Json)


class Log(PrintLog):
    def __init__(self, operation, desired_analyzed_data_information=None):
        self.operation = operation
        self.desired_analyzed_data_information = (
            kline_desired_informations if not
            desired_analyzed_data_information
            else desired_analyzed_data_information)
    #    self.results_from = None
    #    self.last_analyzed_data = None
    #    self.analysis_result = None
    #    self.results_from = None

    @db_session
    def update(self):
        if env.print_log:
            self.print_log()

        self.last_analyzed_data.KlinesDateTime.from_human_readable_to_timestamp()

        last_analyzed_data = [float(getattr(
            self.last_analyzed_data, information).item())
            for information in
            self.desired_analyzed_data_information]

        if self.operation.mode == PossibleModes.BackTesting:

            self.operation.logs.create(
                claimed_at=pendulum.now().int_timestamp,
                analyzed_by=self.analyzed_by,
                last_analyzed_data=last_analyzed_data,
                analysis_result=json.dumps(self.analysis_result))


class TradeLog(db.Entity, AttributeUpdater):
    user = Optional(User)  # Foreing key
    operation_id = Optional(int)
    timestamp = Optional(int)
    signal = Optional(str)
    price = Optional(float)
    fee = Optional(float)  # base_asset units
    base_amount = Optional(float)


class TradesRegister:
    def __init__(self, operation):
        self.operation = operation
        self.storage = Storage(
            db_name=env._DbPath,
            table_name="operation_id_{}_trades".format(self.operation.id),
            primary_key="timestamp")

        self.timestamp = None
        self.signal = None
        self.base_asset_amount = None
        self.price = None
        self.fee = None  # base_asset units

    def save_trade(self):
        pass


db.generate_mapping(create_tables=True)
