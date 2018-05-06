# Copyright (C) 2017, Philsong <songbohr@gmail.com>
# Copyright (C) 2018, geektau <geektau@gmail.com>

from decimal import Decimal
from .broker import Broker, TradeException
import logging
import config
from exchanges.bittrex import Client
 

class Bittrex(Broker):
    def __init__(self, pair_code, api_key=None, api_secret=None):
        super().__init__(pair_code)

        self.client = Client(
            api_key if api_key else config.BITTREX_API_KEY,
            api_secret if api_secret else config.BITTREX_SECRET_KEY)
        self.symbol = self.base_currency + '-' + self.market_currency

        # self.get_balances()

    def _buy_limit(self, amount, price):
        """Create a buy limit order"""
        res = self.client.buy_limit(self.symbol, amount, price)
        return res['result']['uuid']

    def _sell_limit(self, amount, price):
        """Create a sell limit order"""
        res = self.client.sell_limit(self.symbol, amount, price)
        return res['result']['uuid']

    def _order_status(self, res):
        resp = {}
        resp['order_id'] = res['OrderUuid']
        resp['amount'] = float(res['Quantity'])
        resp['price'] = float(res['Limit'])
        resp['deal_amount'] = float(res['Quantity']) - float(res['QuantityRemaining'])
        resp['avg_price'] = float(res['Price'])

        if res['IsOpen']:
            resp['status'] = 'OPEN'
        else:
            resp['status'] = 'CLOSE'

        return resp

    def _get_order(self, order_id):
        res = self.client.get_order(order_id)
        logging.info('get_order: %s' % res)
        assert str(res['result']['OrderUuid']) == str(order_id)
        return self._order_status(res['result'])


    def _cancel_order(self, order_id):
        res = self.client.cancel(order_id)
        if res['success'] == True:
            return True
        else:
            return False

    def _get_balances(self):
        """Get balance"""
        res = self.client.get_balances()
        logging.debug("bittrex get_balances response: %s" % res)

        for entry in res['result']:
            currency = entry['Currency']

            if currency == self.base_currency:
                balance = Decimal(entry['Balance'])
                available = Decimal(entry['Available'])
                frozen = Decimal(entry['Pending'])
                self.balance[self.base_currency] = {
                    'balance': balance,
                    'available': available, 'frozen': frozen
                }
            elif currency == self.market_currency:
                balance = Decimal(entry['Balance'])
                available = Decimal(entry['Available'])
                frozen = Decimal(entry['Pending'])
                self.balance[self.market_currency] = {
                    'balance': balance,
                    'available': available, 'frozen': frozen
                }

        return res

    def test(self):
        order_id = self.buy_limit(0.11, 0.02)
        print(order_id)
        order_status = self.get_order(order_id)
        print(order_status)
        balance = self.get_balances()
        # print(balance)
        cancel_status = self.cancel_order(order_id)
        print(cancel_status)
        order_status = self.get_order(order_id)
        print(order_status)

        order_id = self.sell_limit(0.12, 0.15)
        print(order_id)
        order_status = self.get_order(order_id)
        print(order_status)

        balance = self.get_balances()
        # print(balance)

        cancel_status = self.cancel_order(order_id)
        print(cancel_status)
        order_status = self.get_order(order_id)
        print(order_status)
