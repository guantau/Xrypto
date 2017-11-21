from observers.hedge import Hedge
class Hedge_ETH(Hedge):
    def __init__(self):
        super().__init__(mm_market='KKEX_ETH_BTC',
                         refer_markets=['Bitfinex_ETH_BTC'],
                         hedge_market='Bitfinex_ETH_BTC')
