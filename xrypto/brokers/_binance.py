# Copyright (C) 2017, Philsong <songbohr@gmail.com>
# Copyright (C) 2018, geektau <geektau@gmail.com>

import logging
from decimal import Decimal
import config
from exchanges.binance import Client

from .broker import Broker


class Binance(Broker):
    def __init__(self, pair_code, api_key=None, api_secret=None):
        super().__init__(pair_code)

        self.client = Client(
            api_key if api_key else config.BINANCE_API_KEY,
            api_secret if api_secret else config.BINANCE_SECRET_KEY)

        self.symbol = self.market_currency + self.base_currency
        self.info = self.client.get_symbol_info(self.symbol)
        for f in self.info['filters']:
            if f['filterType'] == 'PRICE_FILTER':
                self.minPrice = Decimal(f['minPrice'])
                self.maxPrice = Decimal(f['maxPrice'])
                self.tickSize = Decimal(f['tickSize'])
            elif f['filterType'] == 'LOT_SIZE':
                self.minQty = Decimal(f['minQty'])
                self.maxQty = Decimal(f['maxQty'])
                self.stepSize = Decimal(f['stepSize'])

    def _buy_limit(self, amount, price):
        """Create a buy limit order"""
        if price > self.maxPrice or price  < self.minPrice:
            logging.error('price {} is not in the range {} - {}'.format(price, self.minPrice, self.maxPrice))
            return None

        if amount > self.maxQty or amount < self.minQty:
            logging.error('amount {} is not in the range {} - {}'.format(amount, self.minQty, self.maxQty))
            return None

        params = {'symbol': self.symbol, 'price': price.quantize(self.tickSize),
                  'quantity': amount.quantize(self.stepSize)}
        return self.client.order_limit_buy(**params)

    def _sell_limit(self, amount, price):
        """Create a sell limit order"""
        if price > self.maxPrice or price < self.minPrice:
            logging.error('price {} is not in the range {} - {}'.format(price, self.minPrice, self.maxPrice))
            return None

        if amount > self.maxQty or amount < self.minQty:
            logging.error('amount {} is not in the range {} - {}'.format(amount, self.minQty, self.maxQty))
            return None

        params = {'symbol': self.symbol, 'price': price.quantize(self.tickSize),
                  'quantity': amount.quantize(self.stepSize)}
        return self.client.order_limit_sell(**params)

    def _order_status(self, res):
        resp = {}
        resp['order_id'] = res['orderId']
        resp['amount'] = Decimal(res['origQty'])
        resp['price'] = Decimal(res['price'])
        resp['deal_amount'] = Decimal(res['executedQty'])
        resp['avg_price'] = Decimal(res['price'])

        if res['status'] == ORDER_STATUS_NEW or res['status'] == ORDER_STATUS_PARTIALLY_FILLED:
            resp['status'] = 'OPEN'
        else:
            # ORDER_STATUS_FILLED, ORDER_STATUS_CANCELED, ORDER_STATUS_PENDING_CANCEL,
            # ORDER_STATUS_REJECTED, ORDER_STATUS_EXPIRED
            resp['status'] = 'CLOSE'

        return resp

    def _get_order(self, order_id):
        res = self.client.get_order(orderId=int(order_id), symbol=self.symbol)
        logging.info('get_order: %s' % res)

        assert str(res['symbol']) == str(self.symbol)
        assert str(res['orderId']) == str(order_id)
        return self._order_status(res)

    def _cancel_order(self, order_id):
        res = self.client.cancel_order(orderId=int(order_id), symbol=self.symbol)
        logging.info('cancel_order: %s' % res)

        assert str(res['orderId']) == str(order_id)
        return True

    def _get_balances(self):
        """Get balance"""
        res = self.client.get_account()
        logging.debug("get_balances: %s" % res)

        for entry in res['balances']:
            currency = entry['asset'].upper()

            if currency == self.base_currency:
                available = Decimal(entry['free'])
                frozen = Decimal(entry['locked'])
                self.balance[self.base_currency] = {
                    'balance': available + frozen,
                    'available': available, 'frozen': frozen
                }
            elif currency == self.market_currency:
                available = Decimal(entry['free'])
                frozen = Decimal(entry['locked'])
                self.balance[self.market_currency] = {
                    'balance': available + frozen,
                    'available': available, 'frozen': frozen
                }

        return res
