# Copyright (C) 2017, Philsong <songbohr@gmail.com>
# Copyright (C) 2018, geektau <geektau@gmail.com>

import logging
import json
from decimal import Decimal
from exchanges.gateio import Client
import config

from .broker import Broker


API_QUERY_URL = 'data.gateio.io'
API_TRADE_URL = 'api.gateio.io'


class Gateio(Broker):
    def __init__(self, pair_code, api_key=None, api_secret=None):

        super().__init__(pair_code)

        self.client = Client(
            url=API_TRADE_URL,
            apiKey=api_key if api_key else config.GATEIO_API_KEY,
            secretKey=api_secret if api_secret else config.GATEIO_SECRET_KEY)

        self.symbol = pair_code

    def _buy_limit(self, amount, price):
        """Create a buy limit order"""
        res = self.client.buy(self.symbol, price, amount)

        logging.info('_buy_limit: %s' % res)

        return res['orderNumber']

    def _sell_limit(self, amount, price):
        """Create a sell limit order"""
        res = self.client.sell(self.symbol, price, amount)

        logging.info('_sell_limit: %s' % res)

        return res['orderNumber']

    def _order_status(self, res):
        resp = {}
        resp['order_id'] = res['orderNumber']
        resp['amount'] = Decimal(res['amount'])
        resp['price'] = Decimal(res['rate'])
        resp['deal_amount'] = Decimal(res['filledAmount'])
        resp['avg_price'] = Decimal(res['filledRate'])

        if res['status'] == 'open':
            resp['status'] = 'OPEN'
        else:
            resp['status'] = 'CLOSE'

        return resp

    def _get_order(self, order_id):
        res = self.client.getOrder(order_id, self.symbol)

        logging.info('get_order: %s' % res)

        assert str(res['order']['id']) == str(order_id)

        return self._order_status(res['order'])

    def _get_orders(self, order_ids):
        orders = []

        for order_id in order_ids:
            res = self._get_order(order_id)
            orders.append(res['data'])

        return orders

    def _cancel_order(self, order_id):
        res = self.client.cancelOrder(order_id, self.symbol)
        logging.info('cancel_order: %s' % res)

        if res['result'] == 'true':
            return True
        else:
            return False

    def _get_balances(self):
        """Get balance"""
        res = json.loads(self.client.balances())

        if self.base_currency in res['available']:
            available = Decimal(res['available'][self.base_currency])
            frozen = Decimal(res['locked'][self.base_currency])
            self.balance[self.base_currency] = {'balance': available+frozen, 'available': available, 'frozen': frozen}

        if self.market_currency in res['available']:
            available = Decimal(res['available'][self.market_currency])
            frozen = Decimal(res['locked'][self.market_currency])
            self.balance[self.market_currency] = {'balance': available + frozen, 'available': available, 'frozen': frozen}

        logging.debug(self)
        return self.balance

    def _get_orders_history(self):
        orders = []
        res = self.client.tradeHistory(self.symbol)
        for order in res['trades']:
            orders.append(order)

        return orders
