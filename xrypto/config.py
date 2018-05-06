markets = [
# "Bitfinex_BCH_BTC",
# "Bittrex_BCH_BTC",
# "KKEX_BCH_BTC",
]

# observers if any
# ["Logger", "TraderBot", "TraderBotSim", "HistoryDumper", "Emailer", "SpecializedTraderBot"]
observers = ["Logger"]

market_expiration_time = 120  # in seconds: 2 minutes

refresh_rate = 5

trade_wait = 10

RISK_PROTECT_MAX_VOLUMN = 100

# liquid strategy parameters config
LIQUID_MAX_AMOUNT = 1
LIQUID_MIN_AMOUNT = 0.1

LIQUID_MAX_BCH_AMOUNT = 1
LIQUID_MIN_BCH_AMOUNT = 0.1

LIQUID_BUY_ORDER_PAIRS = 5
LIQUID_SELL_ORDER_PAIRS = 5
LIQUID_INIT_DIFF = 0.03 #3%
LIQUID_MAX_DIFF = 0.05 #5%
LIQUID_MIN_DIFF = 0.01 #1%
LIQUID_HEDGE_MIN_AMOUNT = 0.001

# arbitrage config
btc_profit_thresh = 0.001  # in BTC
btc_perc_thresh = 0.01  # in 0.01%
bch_max_tx_volume = 5  # in BCH
bch_min_tx_volume = 0.5  # in BCH
bch_frozen_volume = 10

price_departure_perc = 0.002 #in BTC 1%


Diff = 1.001 # 0.1 % arbitrage to execute

TFEE = 1.003 # 1+3*0.001

FEE = 1.0025 # fee for every trade (0.25%)

MAKER_TRADE_ENABLE = False
TAKER_TRADE_ENABLE = True
# maker
MAKER_MAX_VOLUME = 30
MAKER_MIN_VOLUME = 1
MAKER_BUY_QUEUE = 3
MAKER_BUY_STAGE = 1
MAKER_SELL_QUEUE = 3
MAKER_SELL_STAGE = 2

TAKER_MAX_VOLUME = 20
TAKER_MIN_VOLUME = 0.01

bid_fee_rate = 0.001
ask_fee_rate = 0.001
bid_price_risk = 0
ask_price_risk = 0

#hedger

reverse_profit_thresh = 1
reverse_perc_thresh = 0.01
reverse_max_tx_volume = 1  # in BTC

stage0_percent=0.1
stage1_percent=0.2

BUY_QUEUE = 1
SELL_QUEUE = 1

#stata
cny_init = 60000000000
btc_init = 1200000
price_init = 4450

#### Emailer Observer Config
send_trade_mail = False

EMAIL_HOST = 'mail.FIXME.com'
EMAIL_HOST_USER = 'FIXME@FIXME.com'
EMAIL_HOST_PASSWORD = 'FIXME'
EMAIL_USE_TLS = True

EMAIL_RECEIVER = ['FIXME@FIXME.com']

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s [%(threadName)s:%(thread)d] [%(name)s:%(lineno)d] [%(module)s:%(funcName)s] [%(levelname)s]- %(message)s',
            'datefmt': "%Y/%b/%d %H:%M:%S"
        },
        'simple': {
            'format': '%(levelname)s|%(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'info': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'info.log',
            'maxBytes': 1024 * 1024 * 5,  # 5MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'warn': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'warning.log',
            'maxBytes': 1024 * 1024 * 5,  # 5MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'error': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'error.log',
            'maxBytes': 1024 * 1024 * 5,  # 5MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        # This is the "catch all" logger
        '': {
            'handlers': ['console', 'info', 'warn', 'error'],
            'level': 'DEBUG',
            'propagate': False,
        },
    }
}


#### Trader Bot Config
# Access to exchange APIs
HUOBI_API_KEY = ''
HUOBI_SECRET_KEY = ''

OKEX_API_KEY = ''
OKEX_SECRET_KEY = ''

BITTREX_API_KEY = ''
BITTREX_SECRET_KEY = ''

BINANCE_API_KEY = ''
BINANCE_SECRET_KEY = ''

GATEIO_API_KEY = ''
GATEIO_SECRET_KEY = ''

KUCOIN_API_KEY = ''
KUCOIN_SECRET_KEY = ''


SUPPORT_ZMQ = False
ZMQ_HOST = "127.0.0.1"
ZMQ_PORT = 18031

SUPPORT_WEBSOCKET = False
WEBSOCKET_HOST = 'http://localhost'
WEBSOCKET_PORT = 13001

ENV = 'local'

kafka_topic = 'df-depth-replicated'
bootstrap_servers = 'localhost:9092'

try:
    from local_config import *
except ImportError:
    pass

