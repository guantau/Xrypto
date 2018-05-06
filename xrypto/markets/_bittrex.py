# Copyright (C) 2017, Philsong <songbohr@gmail.com>
# Copyright (C) 2018, geektau <geektau@gmail.com>

from decimal import Decimal
from exchanges.bittrex import Client

from .market import Market


class Bittrex(Market):
    def __init__(self,  pair_code):
        super().__init__(pair_code, 0.0025)

        self.client = Client(None, None)
        self.symbol = self.base_currency + '-' + self.market_currency

    def update_depth(self):
        raw_depth = self.client.get_orderbook(self.symbol)
        self.depth = self.format_depth(raw_depth)

    # override method
    def sort_and_format(self, l, reverse=False):
        l.sort(key=lambda x: Decimal(str(x['Rate'])), reverse=reverse)
        r = []
        for i in l:
            r.append({'price': Decimal(str(i['Rate'])), 'amount': Decimal(str(i['Quantity']))})
        return r

    # override method
    def format_depth(self, depth):
        bids = self.sort_and_format(depth['result']['buy'], True)
        asks = self.sort_and_format(depth['result']['sell'], False)
        return {'asks': asks, 'bids': bids}
