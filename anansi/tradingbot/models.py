import os
import pendulum
from pony.orm import *
from ..settings import Default, ENVIRONMENT
#from ..share import tools

db = Database()

if ENVIRONMENT == "DEV":
    db_path = "{}/dev_tradingbot.db".format(str(os.getcwd()))
    db.bind('sqlite', db_path, create_db=True)
    # sql_debug(True)


class User(db.Entity):
    first_name = Required(str, unique=True)
    last_name = Optional(str)
    login_displayed_name = Optional(str)
    email = Optional(str)
    operations = Set("Operation", cascade_delete=True)

    @db_session
    def add(first_name: str, last_name="", email=""):
        User(first_name=first_name,
             last_name=last_name,
             login_displayed_name="{}_{}".format(first_name, last_name),
             email=email)

        return User


@db_session
def add_user(first_name: str, last_name="", login_displayed_name="", email=""):
    User(first_name=first_name,
         last_name=last_name,
         login_displayed_name=login_displayed_name,
         email=email)


class Position(db.Entity):
    operation = Optional("Operation")
    side = Optional(str)
    suggested_side = Optional(str)
    exit_reference_price = Optional(float)


class Wallet(db.Entity):
    operation = Required("Operation")
    quote_asset_amount = Optional(float)
    base_asset_amount = Optional(float)


class Operation(db.Entity):
    user = Required("User")
    trader = Required(str, default=Default.trader)
    position = Optional("Position", cascade_delete=True)
    wallet = Optional("Wallet", cascade_delete=True)
    #movements = Set("TradeMovement")

    status = Required(str, default=Default.status)
    mode = Required(str, default=Default.mode)
    bypass_the_signal_if_recently_stopped = Required(bool, default=True)

    exchange = Required(str)
    symbol = Required(str)

    classifier_name = Required(str, default=Default.classifier)
    classifier_parameters = Optional(Json)
    stop_loss_name = Required(str, default=Default.stop_loss)
    stop_loss_parameters = Optional(Json)

    last_round_timestamp = Optional(int)


@db_session
def create_an_operation(user: User, exchange="Binance", symbol="BTCUSDT"):
    Operation(user=user, exchange=exchange, symbol=symbol)


db.generate_mapping(create_tables=True)
