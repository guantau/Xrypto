# Copyright (C) 2016, Philsong <songbohr@gmail.com>
# Copyright (C) 2018, geektau <geektau@gmail.com>


import logging
from exchanges.gateio import Client

from .market import Market

logger = logging.getLogger(__name__)

API_QUERY_URL = 'data.gateio.io'

class Gateio(Market):
    def __init__(self, pair_code):
        super().__init__(pair_code, 0.002)

        self.client = Client(url=API_QUERY_URL, apiKey=None, secretKey=None)
        self.symbol = self.pair_code

        self.event = 'gateio_depth'
        # self.subscribe_depth()

    def update_depth(self):
        raw_depth = self.client.orderBook(self.symbol)
        if raw_depth:
            if raw_depth['result'] == 'true':
                self.depth = self.format_depth(raw_depth)
            else:
                logger.warning('update depth failed')
        else:
            logger.warning('update depth get no data')
