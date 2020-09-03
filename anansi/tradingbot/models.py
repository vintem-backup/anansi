import os
from pony.orm import *
from .mixins import *
from ..settings import Default, ENVIRONMENT
from ..share import tools

db = Database()

if ENVIRONMENT == "DEV":
    _db_path = "{}/anansi.db".format(str(os.getcwd()))
    db.bind('sqlite', _db_path, create_db=True)
    sql_debug(True)


class Customer(db.Entity, CustomerMixin):
    user_name = Required(str, unique=True)
    traders = Set("Trader")
    first_name = Required(str, default=None)
    last_name = Required(str, default=None)
    email = Required(str, unique=True, default=None)

    @db_session
    def alter_name_to(self, new_name):
        self.user_name = new_name


class Position(db.Entity, PositionMixin):
    # TODO: Sobrecarregar menos este objeto, criando o objeto "Events"
    # para o trader
    trader = Optional("Trader")
    side = Optional(str)
    start_time = Optional(int)
    start_price = Optional(float)
    stop_reference_price = Optional(float)
    amount_quote = Optional(float)
    amount_base = Optional(float)


class Trader(db.Entity, TraderMixin):
    status = Required(str, default=Default.status)
    costumer = Required("Customer", columns=["user_name"])
    mode = Required(str, default=Default.mode)
    position = Required("Position")
    exchange = Required(str)
    symbol = Required(str)
    classifier_name = Required(str, default=Default.classifier)
    classifier_parameters = Optional(Json)
    stop_loss_name = Required(str, default=Default.stop_loss)
    stop_loss_parameters = Optional(Json)


db.generate_mapping(create_tables=True)
