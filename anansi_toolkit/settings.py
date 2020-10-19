import os

# TODO: Change to environs
def GetEnvironment(var_name, default):
    try:
        return os.environ[var_name]
    except:
        try:
            return default
        except KeyError:
            pass

AUTO_START = GetEnvironment("AUTO_START", default=False)


class Environments:

    class Dev:
        print_log = True
        SqlDebug = False
        _DbPath = "{}/dev_tradingbot.db".format(str(os.getcwd()))
        ORM_bind_to = dict(provider='sqlite', filename=_DbPath, create_db=True)

    class Staging:
        print_log = False
        SqlDebug = False
        ORM_bind_to = dict(provider='postgres', user='',
                           password='', host='', database='')

    class Production:
        print_log = False
        SqlDebug = False
        ORM_bind_to = dict(provider='postgres', user='',
                           password='', host='', database='')

    ENV = Dev


class SupportedExchanges:
    binance = "Binance"


class ImplementedTraders:
    SimpleKlinesTrader = "SimpleKlinesTrader"


class ImplementedClassifiers:
    CrossSMA = "CrossSMA"


class ImplementedStopLosses:
    StopTrailing3T = "StopTrailing3T"


class PossibleStatuses:
    Running = "Running"
    NotRunning = "NotRunning"


class PossibleModes:
    Advisor = "Advisor"
    BackTesting = "BackTesting"
    RealTrading = "RealTrading"
    RealTimeTest = "RealTimeTest"


class PossibleSides:
    Zeroed = "Zeroed"
    Long = "Long"
    Short = "Short"


class PossibleSignals:
    SkippedDueToStopLoss = "SkippedDueToStopLoss"
    Hold = "Hold"
    Buy = "Buy"
    Sell = "Sell"
    NakedSell = "NakedSell"
    DoubleSell = "DoubleSell"
    DoubleBuy = "DoubleBuy"
    StopFromLong = "StopFromLong"
    StopFromShort = "StopFromShort"


class PossibleOrderTypes:
    Market = "market"
    Limit = "limit"


class Default:
    trader = ImplementedTraders.SimpleKlinesTrader
    classifier = ImplementedClassifiers.CrossSMA
    stop_loss = ImplementedStopLosses.StopTrailing3T
    status = PossibleStatuses.NotRunning
    mode = PossibleModes.BackTesting
    exchange = SupportedExchanges.binance
    quote_symbol = "BTC"
    base_symbol = "USDT"
    side = PossibleSides.Zeroed
    initial_base_amount = 100.00
    # NakedSell, DoubleBuy and DoubleSell, if allowed, must be declared below
    # (like strings); example: [PossibleSignals.NakedSell] or ["NakedSell"]
    allowed_special_signals = []

kline_desired_informations = [
    "Open_time",
    "Open",
    "High",
    "Low",
    "Close",
    "Volume",
]  # , "Close_time"]


class BinanceSettings:
    api_key = GetEnvironment("binance_api_key", default=None)
    api_secret = GetEnvironment("binance_api_secret", default=None)
    DateTimeFmt = 'timestamp'
    DateTimeUnit = 'milliseconds'
    _base_endpoint = "https://api.binance.com/api/v3/"
    _ping_endpoint = _base_endpoint + "ping"
    _time_endpoint = _base_endpoint + "time"
    _klines_endpoint = _base_endpoint + "klines?symbol={}&interval={}"
    _request_weight_per_minute = 1100  # Default: 1200/min/IP
    records_per_request = 500  # Default: 500 | Limit: 1000 samples/response
    minimal_time_frame = "1m"
    fee_rate_decimal = 0.001
    kline_informations = [
        # Which information (in order), about each candle,
        # is returned by Binance
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
