# Copyright (C) 2017, Philsong <songbohr@gmail.com>

from .broker import Broker, TradeException
import config
import logging
from exchanges.yunbi.client import YunbiClient

# python3 xrypto/cli.py -m Bitfinex_BCH_BTC get-balance

class Yunbi(Broker):
    def __init__(self, base_currency, market_currency, pair_code, api_key=None, api_secret=None):
        super().__init__(base_currency, market_currency, pair_code)

        self.orders = {}

        self.client = YunbiClient(
                    api_key if api_key else config.Viabtc_API_KEY,
                    api_secret if api_secret else config.Viabtc_SECRET_TOKEN)
 
    def _buy_limit(self, amount, price):
        """Create a buy limit order"""
        res = self.client.buy_limit(
            market=self.pair_code,
            amount=str(amount),
            price=str(price)
            )

        logging.verbose('_buy_limit: %s' % res)

        return res['data']['id']

    def _sell_limit(self, amount, price):
        """Create a sell limit order"""
        res = self.client.sell_limit(
            market=self.pair_code,
            amount=str(amount),
            price=str(price))
        logging.verbose('_sell_limit: %s' % res)

        return res['data']['id']

    def _order_status(self, res):
        resp = {}
        resp['order_id'] = res['id']
        resp['amount'] = float(res['amount'])
        resp['price'] = float(res['price'])
        resp['deal_amount'] = float(res['deal_amount'])
        resp['avg_price'] = float(res['avg_price'])

        if res['status'] == 'not_deal' or res['status'] == 'part_deal':
            resp['status'] = 'OPEN'
        else:
            resp['status'] = 'CLOSE'

        return resp

    def _get_order(self, order_id):
        res = self.client.get_order(int(order_id))
        logging.verbose('get_order: %s' % res)

        if res['code'] == 600:
            res = self.orders[order_id]
            res['status'] = 'CLOSE'
            del self.orders[order_id]
            return res

        assert str(res['data']['id']) == str(order_id)
        return self._order_status(res['data'])

    def _cancel_order(self, order_id):
        res = self.client.cancel_order(int(order_id))
        logging.verbose('cancel_order: %s' % res)

        assert str(res['data']['id']) == str(order_id)

        resp = self._order_status(res['data'])
        if res['code'] == 0:
            self.orders[order_id] = resp
        return True

    def _get_balances(self):
        """Get balance"""
        res = self.client.get_balances()
        logging.debug("get_balances: %s" % res)

        entry = res['data']

        self.bch_available = float(entry['BCC']['available'])
        self.bch_balance = float(entry['BCC']['available']) + float(entry['BCC']['frozen'])
        self.btc_available = float(entry['BTC']['available'])
        self.btc_balance = float(entry['BTC']['available']) + float(entry['BTC']['frozen'])
        self.cny_available = float(entry['CNY']['available'])
        self.cny_balance = float(entry['CNY']['available']) + float(entry['CNY']['frozen'])

        return res
