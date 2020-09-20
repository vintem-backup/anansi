# import pandas as pd
import json
from pony.orm import *
from ..settings import Default, Environments
from ..share.tools import Printers
from ..share.db_handlers import LogStorage
from tabulate import tabulate

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
    login_displayed_name = Optional(str)
    email = Optional(str)
    operations = Set("Operation", cascade_delete=True)
    wallet = Required("Wallet", cascade_delete=True)


class Wallet(db.Entity, AttributeUpdater):
    user = Optional("User")
    assets = Optional(Json)


class Position(db.Entity, AttributeUpdater):
    operation = Optional("Operation")
    side = Required(str, default=Default.side)
    quote_amount = Optional(float)
    exit_reference_price = Optional(float)
    due_the_signal = Optional(str)


class Classifier(db.Entity, AttributeUpdater):
    operation = Optional("Operation")
    name = Required(str)
    parameters = Optional(Json)


class StopLoss(db.Entity, AttributeUpdater):
    operation = Optional("Operation")
    name = Required(str)
    parameters = Optional(Json)


class Market(db.Entity):
    operation = Optional("Operation")
    exchange = Required(str, default=Default.exchange)
    quote_asset_symbol = Required(str, default=Default.quote_asset_symbol)
    base_asset_symbol = Required(str, default=Default.base_asset_symbol)


class LastCheck(db.Entity, AttributeUpdater):
    Operation = Optional("Operation")
    by = Optional(str)  # Classifier or StopLoss name
    at = Optional(int)  # timestamp


class Operation(db.Entity, AttributeUpdater):
    user = Required("User")
    trader = Required(str, default=Default.trader)
    position = Required("Position", cascade_delete=True)
    market = Required("Market", cascade_delete=True)
    classifier = Required("Classifier", cascade_delete=True)
    stop_loss = Required("StopLoss", cascade_delete=True)

    status = Required(str, default=Default.status)
    mode = Required(str, default=Default.mode)
    stop_on = Required(bool, default=True)
    hold_if_stopped = Required(bool, default=True)

    last_check = Required("LastCheck")


class Logger(Printers):
    def __init__(self, operation):
        self.operation = operation
        self.storage = LogStorage(
            table_name="log_operation_id_{}".format(self.operation.id))

        self.last_analyzed_data = None
        self.analysis_result = None
        self.results_from = None

    def consolidate_log(self):
        if env.print_log:
            self.print_log()

        self.last_analyzed_data.ParseTime.from_human_readable_to_timestamp()
        log = self.last_analyzed_data.assign(
            results=json.dumps(self.analysis_result))

        self.storage.append_dataframe(log)

    def get_from_db(self, number_of_lines):
        pass

    def show(self, number_of_lines):
        pass


class Movement:
    signal = None
    base_asset_amount = None
    timestamp = None
    price = None
    fee = None


db.generate_mapping(create_tables=True)
