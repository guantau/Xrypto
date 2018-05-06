# Copyright (C) 2017, Philsong <songbohr@gmail.com>
# Copyright (C) 2018, geektau <geektau@gmail.com>

import logging
from ._binance import Binance
from ._bittrex import Bittrex
from ._gateio import Gateio
from ._huobi import Huobi
from ._kucoin import Kucoin

def create_brokers(exchangeNames):
    brokers = {}
    for name in exchangeNames:
        exchange, market_currency, base_currency = name.split('_')
        pair_code = market_currency+'_'+base_currency

        if (exchange == 'BINANCE'):
            xchg = Binance(pair_code)
        elif (exchange == 'BITTREX'):
            xchg = Bittrex(pair_code)
        elif (exchange == 'GATEIO'):
            xchg = Gateio(pair_code)
        elif (exchange == 'HUOBI'):
            xchg = Huobi(pair_code)
        elif (exchange == 'KUCOIN'):
            xchg = Kucoin(pair_code)
        else:
            logging.warning('Exchange ' + name + ' not supported!')
            assert(False)
        logging.info('%s broker initialized' % (xchg.name))

        brokers[name]= xchg

    return brokers
