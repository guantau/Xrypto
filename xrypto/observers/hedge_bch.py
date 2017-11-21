from observers.hedge import Hedge
class Hedge_BCH(Hedge):
    def __init__(self):
        super().__init__(mm_market='KKEX_BCH_BTC',
                         refer_markets=['Bitfinex_BCH_BTC'],
                         hedge_market='Bitfinex_BCH_BTC')
