# Copyright (C) 2017, Philsong <songbohr@gmail.com>
# Copyright (C) 2018, geektau <geektau@gmail.com>

from exchanges.binance import Client

from .market import Market


class Binance(Market):
    def __init__(self, pair_code):
        super().__init__(pair_code, 0.001)

        self.client = Client(None, None)
        self.symbol = self.market_currency + self.base_currency

    def update_depth(self):
        raw_depth = self.client.get_order_book(symbol=self.symbol)
        self.depth = self.format_depth(raw_depth)
