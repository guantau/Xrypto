# Copyright (C) 2017, Philsong <songbohr@gmail.com>

import logging
import requests
from .market import Market
from exchanges.kkex_api import Client


class KKEX(Market):
    def __init__(self, pair_code):
        base_currency, market_currency = self.get_tradeable_pairs(pair_code)

        super().__init__(base_currency, market_currency, pair_code, 0.001)

        self.client = Client(None, None)

    def update_depth(self):
        raw_depth = self.client.depth(symbol=self.pair_code)
        self.depth = self.format_depth(raw_depth)

    def get_tradeable_pairs(self, pair_code):
        if pair_code == 'BCHBTC':
            base_currency = 'BTC'
            market_currency = 'BCH'
        elif pair_code == 'ETHBTC':
            base_currency = 'BTC'
            market_currency = 'ETH'
        else:
            assert(False)
        return base_currency, market_currency
