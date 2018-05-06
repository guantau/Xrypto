# Copyright (C) 2017, Philsong <songbohr@gmail.com>
# Copyright (C) 2018, geektau <geektau@gmail.com>

from decimal import Decimal
from exchanges.kucoin import Client

from .market import Market


class Kucoin(Market):
    def __init__(self,  pair_code):
        super().__init__(pair_code, 0.0025)

        self.client = Client(api_key='', api_secret='')
        self.symbol = self.market_currency + '-' + self.base_currency

    def update_depth(self):
        raw_depth = self.client.get_order_book(self.symbol)
        self.depth = self.format_depth(raw_depth)

    # override method
    def format_depth(self, depth):
        bids = self.sort_and_format(depth['BUY'], True)
        asks = self.sort_and_format(depth['SELL'], False)
        return {'asks': asks, 'bids': bids}
