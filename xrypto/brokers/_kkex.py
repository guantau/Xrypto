# Copyright (C) 2017, Philsong <songbohr@gmail.com>

from .broker import Broker, TradeException
import logging
from xrypto.exchanges.kkex_api import Client

class KKEX(Broker):
    def __init__(self, pair_code, api_key=None, api_secret=None):
        
        base_currency, market_currency = self.get_tradeable_pairs(pair_code)

        super().__init__(base_currency, market_currency, pair_code)
        
        self.client = Client(
                    api_key,
                    api_secret)
 
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

    def _buy_limit(self, amount, price):
        """Create a buy limit order"""
        res = self.client.buy_limit(
            symbol=self.pair_code,
            amount=str(amount),
            price=str(price))

        logging.verbose('_buy_limit: %s' % res)

        return res['order_id']

    def _sell_limit(self, amount, price):
        """Create a sell limit order"""
        res = self.client.sell_limit(
            symbol=self.pair_code,
            amount=str(amount),
            price=str(price))
        logging.verbose('_sell_limit: %s' % res)

        return res['order_id']

    def _order_status(self, res):
        resp = {}
        resp['order_id'] = res['order_id']
        resp['amount'] = float(res['amount'])
        resp['price'] = float(res['price'])
        resp['deal_amount'] = float(res['deal_amount'])
        resp['avg_price'] = float(res['avg_price'])
        resp['type'] = res['type']

        if res['status'] == 0 or res['status'] == 1 or res['status'] == 4:
            resp['status'] = 'OPEN'
        else:
            resp['status'] = 'CLOSE'

        return resp

    def _get_order(self, order_id):
        res = self.client.order_info(self.pair_code, int(order_id))
        logging.verbose('get_order: %s' % res)

        assert str(res['order']['order_id']) == str(order_id)
        return self._order_status(res['order'])

    def _get_orders(self, order_ids):
        orders = []
        res = self.client.orders_info(self.pair_code, order_ids) 

        for order in res['orders']:
            resp_order = self._order_status(order)
            orders.append(resp_order)
                  
        return orders

    def _cancel_order(self, order_id):
        res = self.client.cancel_order(self.pair_code, int(order_id))
        logging.verbose('cancel_order: %s' % res)

        assert str(res['order_id']) == str(order_id)

        return True

    def _get_balances(self):
        """Get balance"""
        res = self.client.get_userinfo()
        logging.verbose("kkex get_balances: %s" % res)

        entry = res['info']['funds']

        self.bch_available = float(entry['free']['BCH'])
        self.bch_balance = float(
            entry['freezed']['BCH']) + float(entry['free']['BCH'])
        self.btc_available = float(entry['free']['BTC'])
        self.btc_balance = float(entry['freezed']['BTC']) + float(entry['free']['BTC'])

        return res

    def _get_orders_history(self):
        orders = []
        res = self.client.get_orders_history(self.pair_code, pagesize=200)   
        # logging.debug('res: %s', res) 
        for order in res['orders']:
            resp_order = self._order_status(order)
            orders.append(resp_order)
                  
        return orders
