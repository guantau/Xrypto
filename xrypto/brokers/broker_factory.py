import logging
import xrypto.config as config
from xrypto.brokers._kkex import KKEX
from xrypto.brokers._bittrex import Bittrex
from xrypto.brokers._bitfinex import Bitfinex
from xrypto.brokers._viabtc import Viabtc

def create_brokers(exchangeNames):
    brokers = {}
    for name in exchangeNames:
        if (name == 'KKEX_BCH_BTC'):
            xchg = KKEX('BCCBTC', config.KKEX_API_KEY, config.KKEX_SECRET_TOKEN)
        elif (name == 'KKEX_ETH_BTC'):
            xchg = KKEX('ETHBTC', config.KKEX_API_KEY, config.KKEX_SECRET_TOKEN)
        elif (name == 'Bitfinex_BCH_BTC'):
            xchg = Bitfinex('bchbtc', config.Bitfinex_API_KEY, config.Bitfinex_SECRET_TOKEN)
        elif (name == 'Bittrex_BCH_BTC'):
            xchg = Bittrex('BTC-BCC', config.Bittrex_API_KEY, config.Bittrex_SECRET_TOKEN)
        elif (name == 'Viabtc_BCH_BTC'):
            xchg = Viabtc('bccbtc', config.Viabtc_API_KEY, config.Viabtc_SECRET_TOKEN)
        elif (name == 'Viabtc_BCH_CNY'):
            xchg = Viabtc('bcccny', config.Viabtc_API_KEY, config.Viabtc_SECRET_TOKEN)
        elif (name == 'Viabtc_BTC_CNY'):
            xchg = Viabtc('btccny', config.Viabtc_API_KEY, config.Viabtc_SECRET_TOKEN)
        else:
            logging.warn('Exchange ' + name + ' not supported!')
            assert(False)
        logging.info('%s broker initialized' % (xchg.name))

        brokers[name]= xchg
    return brokers
