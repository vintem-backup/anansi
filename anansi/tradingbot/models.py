import os
import pendulum
from pony.orm import *
from .mixins import *
from ..settings import Default, ENVIRONMENT
from ..share import tools

db = Database()

if ENVIRONMENT == "DEV":
    _db_path = "{}/anansi.db".format(str(os.getcwd()))
    db.bind('sqlite', _db_path, create_db=True)
    sql_debug(True)


class Customer(db.Entity):
    user_name = Required(str, unique=True)
    operations = Set("Operation")
    first_name = Required(str, default=None)
    last_name = Required(str, default=None)
    email = Required(str, unique=True, default=None)

    @db_session  # !Isto é só um teste de método que altera entrada no DB
    def alter_name_to(self, new_name):
        self.user_name = new_name

    def get_name(self):  # !Isto é só um teste de método qualquer
        return "{}".format(self.user_name)


class Position(db.Entity):
    operation = Optional("Operation")
    side = Optional(str)
    suggested_side = Optional(str)
    exit_reference_price = Optional(float)


class Wallet(db.Entity):
    operation = Optional("Operation")
    quote_asset_amount = Optional(float)
    base_asset_amount = Optional(float)


class TradeMovement(db.Entity):
    operation = Optional("Operation")
    direction = Optional(str)  # buy, sell, naked_sell, n_buy (levarege), etc
    enter_base_asset_amount = Optional(float)
    enter_timestamp = Optional(int)
    enter_price = Optional(float)
    enter_fee = Optional(float)  # base asset units
    exit_base_asset_amount = Optional(float)
    exit_timestamp = Optional(int)
    exit_price = Optional(float)
    exit_fee = Optional(float)  # base asset units

    # @db_session
    # def movement_enter(self, price, fee):
    #    self.enter_timestamp, self.enter_price, self.enter_fee = (
    #        pendulum.now().int_timestamp, price, fee)

    # @db_session
    # def movement_exit(self, price, fee):
    #    self.exit_timestamp, self.exit_price, self.exit_fee = (
    #        pendulum.now().int_timestamp, price, fee)


class Operation(db.Entity):  # , TraderMixin):
    costumer = Required("Customer", columns=["user_name"])
    position = Required("Position")
    wallet = Required("Wallet")
    movements = Set("TradeMovements")

    status = Required(str, default=Default.status)
    mode = Required(str, default=Default.mode)

    exchange = Required(str)
    symbol = Required(str)

    classifier_name = Required(str, default=Default.classifier)
    classifier_parameters = Optional(Json)
    stop_loss_name = Required(str, default=Default.stop_loss)
    stop_loss_parameters = Optional(Json)
    last_round_timestamp = Required(int, default=None)


db.generate_mapping(create_tables=True)
