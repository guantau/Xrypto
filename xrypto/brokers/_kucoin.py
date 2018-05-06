# Copyright (C) 2017, Philsong <songbohr@gmail.com>
# Copyright (C) 2018, geektau <geektau@gmail.com>

import logging
import config
from decimal import Decimal
from exchanges.kucoin import Client

from .broker import Broker


class Kucoin(Broker):
    def __init__(self, pair_code, api_key=None, api_secret=None):

        super().__init__(pair_code)

        self.client = Client(
            api_key=api_key if api_key else config.KUCOIN_API_KEY,
            api_secret=api_secret if api_secret else config.KUCOIN_SECRET_KEY)

        self.symbol = self.market_currency + '-' + self.base_currency

    def _buy_limit(self, amount, price):
        """Create a buy limit order"""
        res = self.client.create_buy_order(self.symbol, price, amount)

        logging.info('_buy_limit: %s' % res)

        return res['orderOid']

    def _sell_limit(self, amount, price):
        """Create a sell limit order"""
        res = self.client.create_sell_order(self.symbol, price, amount)

        logging.info('_sell_limit: %s' % res)

        return res['orderOid']

    def _order_status(self, res):
        resp = {}
        resp['order_id'] = res['orderOid']
        resp['amount'] = Decimal(res['pendingAmount']) + Decimal(res['dealAmount'])
        resp['price'] = Decimal(res['orderPrice'])
        resp['deal_amount'] = Decimal(res['dealAmount'])
        resp['avg_price'] = Decimal(res['dealPriceAverage'])

        if res['status'] == 'open':
            resp['status'] = 'OPEN'
        else:
            resp['status'] = 'CLOSE'

        return resp

    def _get_order(self, order_id):
        # TODO: how to get order type
        res = self.client.get_order_details(symbol=self.symbol, order_id=order_id)

        logging.info('get_order: %s' % res)

        assert str(res['data']['orderOid']) == str(order_id)

        return self._order_status(res['data'])

    def _get_orders(self, order_ids):
        orders = []

        for order_id in order_ids:
            res = self._get_order(order_id)
            orders.append(res['data'])

        return orders

    def _cancel_order(self, order_id):
        res = self.client.cancel_order(order_id, self.symbol)
        logging.info('cancel_order: %s' % res)

        if res['success'] == 'true':
            return True
        else:
            return False

    def _get_balances(self):
        """Get balance"""
        res = self.client.get_coin_balance(self.base_currency)
        if res['success'] == 'true':
            balance = Decimal(res['data']['balance'])
            frozen = Decimal(res['data']['freezeBalance'])
            self.balance[self.base_currency] = {'balance': balance, 'available': balance-frozen, 'frozen': frozen}

        res = self.client.get_coin_balance(self.market_currency)
        if res['success'] == 'true':
            balance = Decimal(res['data']['balance'])
            frozen = Decimal(res['data']['freezeBalance'])
            self.balance[self.market_currency] = {'balance': balance, 'available': balance-frozen, 'frozen': frozen}

        logging.debug(self)
        return self.balance

    def _get_orders_history(self):
        orders = []
        res = self.client.get_dealt_orders(self.symbol)
        for order in res['datas']:
            orders.append(order)

        return orders
