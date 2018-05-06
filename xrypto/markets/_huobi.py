# Copyright (C) 2016, Philsong <songbohr@gmail.com>
# Copyright (C) 2018, geektau <geektau@gmail.com>


import logging
from exchanges.huobi import Client

from .market import Market

logger = logging.getLogger(__name__)

class Huobi(Market):
    def __init__(self, pair_code):
        super().__init__(pair_code, 0.002)

        self.client = Client()
        self.symbol = self.market_currency.lower()+self.base_currency.lower()

        self.event = 'huobi_depth'
        # self.subscribe_depth()

    def update_depth(self):
        # step0, step1, step2, step3, step4, step5 (combine depth 0-5)
        raw_depth = self.client.get_depth(self.symbol, 'step0')
        if raw_depth:
            if raw_depth['status'] == 'ok':
                self.depth = self.format_depth({'asks': raw_depth['tick']['asks'],
                                                'bids': raw_depth['tick']['bids']})
            else:
                logger.warning('update depth warning: ' + raw_depth['err-msg'])
        else:
            logger.warning('update depth get no data')
