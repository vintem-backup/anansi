import os
AUTO_START = False


class Environments:

    class Dev:
        print_current_round_log = True
        SqlDebug = False
        _DbPath = "{}/dev_tradingbot.db".format(str(os.getcwd()))
        ORM_bind_to = dict(provider='sqlite', filename=_DbPath, create_db=True)

    class Staging:
        print_current_round_log = False
        SqlDebug = False
        ORM_bind_to = dict(provider='postgres', user='',
                           password='', host='', database='')

    class Production:
        print_current_round_log = False
        SqlDebug = False
        ORM_bind_to = dict(provider='postgres', user='',
                           password='', host='', database='')

    ENV = Dev


class ImplementedTraders:
    DefaultTrader = "DefaultTrader"


class ImplementedClassifiers:
    CrossSMA = "CrossSMA"


class ImplementedStopLosses:
    StopTrailing3T = "StopTrailing3T"


class PossibleStatuses:
    Running = "Running"
    NotRunning = "NotRunning"


class PossibleModes:
    BackTesting = "BackTesting"
    RealTrading = "RealTrading"
    RealTimeTest = "RealTimeTest"


class PossibleSides:
    Zeroed = "Zeroed"
    Long = "Long"
    Short = "Short"
    Classifying = "Classifying"


class PossibleSignals:
    StopPassed = "StopPassed"
    Hold = "Hold"
    Buy = "Buy"
    Sell = "Sell"
    NakedSell = "NakedSell"
    DoubleNakedSell = "DoubleNakedSell"
    DoubleBuy = "DoubleBuy"
    StoppedFromLong = "StoppedFromLong"
    StoppedFromShort = "StoppedFromShort"


class Default:
    trader = ImplementedTraders.DefaultTrader
    classifier = ImplementedClassifiers.CrossSMA
    stop_loss = ImplementedStopLosses.StopTrailing3T
    status = PossibleStatuses.NotRunning
    mode = PossibleModes.BackTesting
    exchange = "Binance"
    ticker_symbol = "BTC"
    quote_symbol = "USDT"
    side = PossibleSides.Zeroed
    initial_assets = {
        'BTC': 0.0,
        'USDT': 100.00}


kline_desired_informations = [
    "Open_time",
    "Open",
    "High",
    "Low",
    "Close",
    "Volume",
]  # , "Close_time"]


# TODO: API key and secret from get os.environment ou default = None
class Binance_:
    api_key = None
    api_secret = None
    DateTimeFmt = 'timestamp'
    DateTimeUnit = 'milliseconds'
    _base_endpoint = "https://api.binance.com/api/v3/"
    _ping_endpoint = _base_endpoint + "ping"
    _time_endpoint = _base_endpoint + "time"
    _klines_endpoint = _base_endpoint + "klines?symbol={}&interval={}"
    _request_weight_per_minute = 1100  # Default: 1200/min/IP
    records_per_request = 500  # Default: 500 | Limit: 1000 samples/response
    minimal_time_frame = "1m"

    kline_informations = [
        # Que informações (em ordem) são retornadas pela Binance em cada candle
        "Open_time",
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
        "Close_time",
        "Quote_asset_volume",
        "Number_of_trades",
        "Taker_buy_base_asset_volume",
        "Taker_buy_quote_asset_volume",
        "Ignore",
    ]
