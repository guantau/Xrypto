from observers.hedge import Hedge
import config

class Hedge_ETH(Hedge):
    def __init__(self):
        super().__init__(currency='ETH',
                         mm_market='KKEX_ETH_BTC',
                         refer_markets=['Bitfinex_ETH_BTC'],
                         hedge_market='Bitfinex_ETH_BTC',
                         max_trade_amount=config.LIQUID_MAX_AMOUNT,
                         min_trade_amount=config.LIQUID_MIN_AMOUNT)
