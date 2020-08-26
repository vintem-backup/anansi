import os
from pony.orm import *
from .mixins import *
from ..settings import Default, ENVIRONMENT
from ..share import tools

db = Database()

if ENVIRONMENT == "DEV":
    _path = "{}/anansi.db".format(str(os.getcwd()))
    db = Database()
    db.bind('sqlite', _path, create_db=True)
    sql_debug(True)


class Customer(db.Entity, CustomerMixin):
    user_name = Required(str, unique=True)
    traders = Set("Trader")
    first_name = Optional(str)
    last_name = Optional(str)
    email = Optional(str, unique=True)


class Position(db.Entity, PositionMixin):
    trader = Optional("Trader")
    side = Optional(str)
    start_at_time = Optional(int)
    start_at_price = Optional(float)
    stop_reference_price = Optional(float)
    amount_quote = Optional(float)
    amount_base = Optional(float)


class Trader(db.Entity, TraderMixin):
    status = Required(str, default=Default.status)
    costumer = Required("Customer", columns=["name"])
    mode = Required(str, default=Default.mode)
    position = Required("Position")
    exchange = Required(str)
    symbol = Required(str)
    classifier_name = Required(str, default=Default.classifier)
    classifier_parameters = Optional(Json)
    stop_loss_name = Required(str, default=Default.stop_loss)
    stop_loss_parameters = Optional(Json)


db.generate_mapping(create_tables=True)

# @db_session
# def add_user(user_)


def populate_db():
    pass
