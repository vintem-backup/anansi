ENVIRONMENT = "DEV"
AUTO_START = False

CrossSMA, StopTrailing3T = "CrossSMA", "StopTrailing3T"

# The possible traders statuses
Running, NotRunning = "Running", "NotRunning"

# The possible modes
BackTesting, RealTrading, RealTimeTest = (
    "BackTesting", "RealTrading", "RealTimeTest"
)


class Default:
    status = NotRunning
    mode = BackTesting
    classifier = CrossSMA
    stop_loss = StopTrailing3T


klines_desired_info = [
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

    kline_information_map = [
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
