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
    quote_asset_amount = Optional(float)
    base_asset_amount = Optional(float)

    def update_current_side_to(self, new_current_side):
        self.current_side = new_current_side
        commit()

    def update_hint_side_to(self, new_hint_side):
        self.hint_side = new_hint_side
        commit()


class Operation(db.Entity):
    user = Required("User")
    trader = Required(str, default=Default.trader)
    position = Required("Position", cascade_delete=True)

    status = Required(str, default=Default.status)
    mode = Required(str, default=Default.mode)
    ignore_stop_loss = Required(bool, default=False)
    bypass_if_recently_stopped = Required(bool, default=True)

    exchange = Required(str, default=Default.exchange)
    symbol = Required(str, default=Default.symbol)

    classifier_name = Required(str, default=Default.classifier)
    classifier_parameters = Optional(Json)
    stop_loss_name = Required(str, default=Default.stop_loss)
    stop_loss_parameters = Optional(Json)

    last_round_timestamp = Optional(int)

    def update_status_to(self, new_status: str):
        self.status = new_status
        commit()

    def update_classifier_parameters_to(self, new_classifier_parameters):
        self.classifier_parameters = new_classifier_parameters
        commit()

    def update_stop_loss_parameters_to(self, new_stop_loss_parameters):
        self.stop_loss_parameters = new_stop_loss_parameters
        commit()


@db_session
def create_operation(**kwargs):
    position = {}

    if not "position" in kwargs.keys():
        position = {
            'position': Position(current_side=side.Zeroed)
        }

    Operation(**{**kwargs, **position})


db.generate_mapping(create_tables=True)
