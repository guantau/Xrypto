import requests
import logging
from hashlib import md5
from urllib.parse import urljoin
from urllib.parse import urlencode

class Client:
    def __init__(self, key, secret, api_root='https://kkex.com'):
        self.key = key
        self.secret = secret
        self.api_root = api_root

    def make_sign(self, params):
        # Simple sign
        sign = list(sorted(params.items()) + [('secret_key', self.secret)])
        signer = md5()
        signer.update(urlencode(sign).encode('utf-8'))
        return signer.hexdigest().upper()

    def trade_api(self, path, params=None):
        if params is None:
            params = {}

        params['api_key'] = self.key
        sign = self.make_sign(params)
        params['sign'] = sign

        url = urljoin(self.api_root, path)
        r = requests.post(url, data=params, timeout=10)
        try:
            return r.json()

        except ValueError as e:
            logging.error("Can't trade_api - err:%s" % str(e))
            logging.error("response:%s" % r.text)
            raise

    def public_api(self, path, params=None):
        url = urljoin(self.api_root, path)
        if params:
            url = '%s?%s' % (url, urlencode(params))
        r = requests.get(url, timeout=10)
        try:
            return r.json()
        except ValueError as e:
            logging.error("Can't public_api - err:%s" % str(e))
            logging.error("response:%s" % r.text)
            raise

    def ticker(self, symbol):
        return self.public_api('/api/v1/ticker',
                            {'symbol': symbol})

    def tickers(self, *symbol):
        return self.public_api('/api/v1/ticker',
                            {'symbol': ','.join(symbols)})

    def depth(self, symbol, size=5, merge=None):
        params = {'symbol': symbol}
        params['size'] = size
        if merge is not None:
            params['merge'] = merge
        return self.public_api('/api/v1/depth', params)

    def get_products(self):
        return self.public_api('/api/v1/products')

    def get_assets(self):
        return self.public_api('/api/v1/assets')

    # ttrade apis
    def get_userinfo(self):
        return self.trade_api('/api/v1/userinfo')

    def get_orders_history(self, symbol, status=0, page=1, pagesize=10):
        params = {
            'symbol': symbol,
            'status': status,
            'current_page': page,
            'page_length': pagesize}
        return self.trade_api('/api/v1/order_history', params)

    def buy_limit(self, symbol, amount, price):
        params = {
            'symbol': symbol,
            'type': 'buy',
            'price': price,
            'amount': amount
        }
        logging.debug(
            'buy limit %s %s %s', symbol, amount, price)
        return self.trade_api('/api/v1/trade', params)

    def sell_limit(self, symbol, amount, price):
        params = {
            'symbol': symbol,
            'type': 'sell',
            'price': price,
            'amount': amount
        }
        logging.debug(
            'sell limit %s %s %s', symbol, amount, price)
        return self.trade_api('/api/v1/trade', params)

    def buy_market(self, symbol, price_amount):
        params = {
            'symbol': symbol,
            'type': 'buy_market',
            'price': str(price_amount)
        }
        logging.debug(
            'buy limit %s %s', symbol, price_amount)
        return self.trade_api('/api/v1/trade', params)

    def sell_market(self, symbol, amount):
        params = {
            'symbol': symbol,
            'type': 'sell_market',
            'amount': amount
        }
        logging.debug(
            'buy limit %s %s', symbol, amount)
        return self.trade_api('/api/v1/trade', params)

    def cancel_order(self, symbol, order_id):
        params = {'symbol': symbol,
                  'order_id': order_id}
        return self.trade_api('/api/v1/cancel_order', params)

    def order_info(self, symbol, order_id):
        params = {'symbol': symbol}
        params['order_id'] = order_id
        return self.trade_api('/api/v1/order_info', params)

    def orders_info(self, symbol, order_ids):
        params = {'symbol': symbol}
        params['order_id'] = ','.join(order_ids)
        return self.trade_api('/api/v1/orders_info', params)
