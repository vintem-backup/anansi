from pony.orm import *
from ..settings import Default, Environments, PossibleSides as side

db, env = Database(), Environments.ENV

db.bind(**env.DbParam)
sql_debug(env.SqlDebug)


class User(db.Entity):
    first_name = Required(str, unique=True)
    last_name = Optional(str)
    login_displayed_name = Optional(str)
    email = Optional(str)
    operations = Set("Operation", cascade_delete=True)

    @db_session
    def update_first_name_to(self, new_first_name):
        self.first_name = new_first_name
        commit()


@db_session
def create_user(**kwargs):
    User(**kwargs)


class Position(db.Entity):
    operation = Optional("Operation")
    current_side = Optional(str)
    hint_side = Optional(str)
    exit_reference_price = Optional(float)


class Wallet(db.Entity):
    operation = Optional("Operation")
    quote_asset_amount = Optional(float)
    base_asset_amount = Optional(float)


class Operation(db.Entity):
    user = Required("User")
    trader = Required(str, default=Default.trader)
    position = Optional("Position", cascade_delete=True)
    wallet = Optional("Wallet", cascade_delete=True)

    status = Required(str, default=Default.status)
    mode = Required(str, default=Default.mode)
    bypass_if_recently_stopped = Required(bool, default=True)

    exchange = Required(str, default=Default.exchange)
    symbol = Required(str, default=Default.symbol)

    classifier_name = Required(str, default=Default.classifier)
    classifier_parameters = Optional(Json)
    stop_loss_name = Required(str, default=Default.stop_loss)
    stop_loss_parameters = Optional(Json)

    last_round_timestamp = Optional(int)

    @db_session
    def update_status_to(self, new_status):
        self.status = new_status
        commit()


@db_session
def create_operation(**kwargs):
    Operation(**kwargs)


db.generate_mapping(create_tables=True)
