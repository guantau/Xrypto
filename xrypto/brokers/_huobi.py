# Copyright (C) 2017, Philsong <songbohr@gmail.com>
# Copyright (C) 2018, geektau <geektau@gmail.com>

import logging
from decimal import Decimal
from exchanges.huobi import Client
import config

from .broker import Broker


class Huobi(Broker):
    def __init__(self, pair_code, api_key=None, api_secret=None):

        super().__init__(pair_code)

        self.client = Client(
            api_key if api_key else config.HUOBI_API_KEY,
            api_secret if api_secret else config.HUOBI_SECRET_KEY)

        self.symbol = self.market_currency.lower() + self.base_currency.lower()

    def _buy_limit(self, amount, price):
        """Create a buy limit order"""
        res = self.client.send_order(
            amount=str(amount),
            source='api',
            symbol=self.symbol,
            _type='buy-limit',
            price=str(price))

        logging.info('_buy_limit: %s' % res)

        return res['data']

    def _sell_limit(self, amount, price):
        """Create a sell limit order"""
        res = self.client.send_order(
            amount=str(amount),
            source='api',
            symbol=self.symbol,
            _type='sell-limit',
            price=str(price))

        logging.info('_sell_limit: %s' % res)

        return res['data']

    def _order_status(self, res):
        resp = {}
        resp['order_id'] = res['id']
        resp['amount'] = Decimal(res['amount'])
        resp['price'] = Decimal(res['price'])
        resp['deal_amount'] = Decimal(res['field-amount'])
        resp['avg_price'] = Decimal(res['field-cash-amount']) / Decimal(res['field-amount'])

        if res['status'] in ['pre-submitted', 'submitting', 'submitted', 'partial-filled']:
            resp['status'] = 'OPEN'
        else:
            # partial-canceled, filled, canceled
            resp['status'] = 'CLOSE'

        return resp

    def _get_order(self, order_id):
        res = self.client.order_info(order_id)

        logging.info('get_order: %s' % res)

        assert str(res['data']['id']) == str(order_id)

        return self._order_status(res['data'])

    def _get_orders(self, order_ids):
        orders = []

        for order_id in order_ids:
            res = self._get_order(order_id)
            orders.append(res['data'])

        return orders

    def _cancel_order(self, order_id):
        res = self.client.cancel_order(order_id)
        logging.info('cancel_order: %s' % res)

        assert str(res['data']) == order_id

        return True

    def _get_balances(self):
        """Get balance"""
        res = self.client.get_balance()

        def get_data(data, currency, type):
            for item in data:
                if item['currency'] == currency.lower() and item['type'] == type:
                    return str(item['balance'])

        available = Decimal(get_data(res['data']['list'], self.base_currency, 'trade'))
        frozen = Decimal(get_data(res['data']['list'], self.base_currency, 'frozen'))
        self.balance[self.base_currency] = {'balance': available+frozen, 'available': available, 'frozen': frozen}

        available = Decimal(get_data(res['data']['list'], self.market_currency, 'trade'))
        frozen = Decimal(get_data(res['data']['list'], self.market_currency, 'frozen'))
        self.balance[self.market_currency] = {'balance': available + frozen, 'available': available, 'frozen': frozen}

        logging.debug(self)
        return self.balance

    def _get_orders_history(self):
        orders = []
        res = self.client.orders_matchresults(self.symbol)
        for order in res['data']:
            orders.append(order)

        return orders
