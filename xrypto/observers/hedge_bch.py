from observers.hedge import Hedge
import config

class Hedge_BCH(Hedge):
    def __init__(self):
        super().__init__(currency = 'BCH',
                         mm_market='KKEX_BCH_BTC',
                         refer_markets=['Bitfinex_BCH_BTC'],
                         hedge_market='Bitfinex_BCH_BTC',
                         max_trade_amount=config.LIQUID_MAX_BCH_AMOUNT,
                         min_trade_amount=config.LIQUID_MIN_BCH_AMOUNT)
                         
