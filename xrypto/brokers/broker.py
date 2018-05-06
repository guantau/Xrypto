# Copyright (C) 2017, Philsong <songbohr@gmail.com>
# Copyright (C) 2018, geektau <geektau@gmail.com>

import logging
import inspect
from prettytable import PrettyTable
from decimal import Decimal

import config


def get_current_function_name():
    return inspect.stack()[1][3]


class TradeException(Exception):
    pass


class Broker(object):
    def __init__(self, pair_code):
        self.name = self.__class__.__name__

        market_currency, base_currency = pair_code.split('_')

        self.base_currency = base_currency.upper()
        self.market_currency = market_currency.upper()

        if (self.base_currency not in ['USDT', 'BTC', 'ETH']):
            logging.error('base currency is {}, only support BTC, ETH, USDT'.format(self.base_currency))
            assert (False)

        self.balance = {
            self.base_currency: {'balance': Decimal('0'), 'available': Decimal('0'), 'frozen': Decimal('0')},
            self.market_currency: {'balance': Decimal('0'), 'available': Decimal('0'), 'frozen': Decimal('0')},
        }

    def __str__(self):
        table = PrettyTable(['Currency', 'Balance', 'Available', 'Frozen'])
        table.add_row([self.base_currency,
                       self.balance[self.base_currency]['balance'],
                       self.balance[self.base_currency]['available'],
                       self.balance[self.base_currency]['frozen']])
        table.add_row([self.market_currency,
                       self.balance[self.market_currency]['balance'],
                       self.balance[self.market_currency]['available'],
                       self.balance[self.market_currency]['frozen']])

        return table.get_string()

    def buy_limit(self, amount, price, client_id=None):
        if amount > config.RISK_PROTECT_MAX_VOLUMN:
            logging.error('risk alert: amount %s > risk amount:%s' % (amount, config.RISK_PROTECT_MAX_VOLUMN))
            return None

        logging.info("BUY LIMIT %f %s at %f %s @%s" % (amount, self.market_currency,
                                                       price, self.base_currency, self.name))

        try:
            if client_id:
                return self._buy_limit(amount, price, client_id)
            else:
                return self._buy_limit(amount, price)
        except Exception as e:
            logging.error('%s %s except: %s' % (self.name, get_current_function_name(), e))
            return None

    def sell_limit(self, amount, price, client_id=None):
        if amount > config.RISK_PROTECT_MAX_VOLUMN:
            logging.error('risk alert: amount %s > risk amount:%s' % (amount, config.RISK_PROTECT_MAX_VOLUMN))
            return None

        logging.info("SELL LIMIT %f %s at %f %s @%s" % (amount, self.market_currency,
                                                        price, self.base_currency, self.name))

        try:
            if client_id:
                return self._sell_limit(amount, price, client_id)
            else:
                return self._sell_limit(amount, price)
        except Exception as e:
            logging.error('%s %s except: %s' % (self.name, get_current_function_name(), e))
            return None

    def buy_maker(self, amount, price):
        if amount > config.RISK_PROTECT_MAX_VOLUMN:
            logging.error('risk alert: amount %s > risk amount:%s' % (amount, config.RISK_PROTECT_MAX_VOLUMN))
            return None

        logging.info("BUY MAKER %f %s at %f %s @%s" % (amount, self.market_currency,
                                                       price, self.base_currency, self.name))

        try:
            return self._buy_maker(amount, price)
        except Exception as e:
            logging.error('%s %s except: %s' % (self.name, get_current_function_name(), e))
            return None

    def sell_maker(self, amount, price):
        if amount > config.RISK_PROTECT_MAX_VOLUMN:
            logging.error('risk alert: amount %s > risk amount:%s' % (amount, config.RISK_PROTECT_MAX_VOLUMN))
            return None

        logging.info("SELL MAKER %f %s at %f %s @%s" % (amount, self.market_currency,
                                                        price, self.base_currency, self.name))
        try:
            return self._sell_maker(amount, price)
        except Exception as e:
            logging.error('%s %s except: %s' % (self.name, get_current_function_name(), e))
            return None

    def get_order(self, order_id):
        if not order_id:
            logging.error('order id is null')
            return None

        try:
            return self._get_order(order_id)
        except Exception as e:
            logging.error('%s %s except: %s' % (self.name, get_current_function_name(), e))
            return None

    def cancel_order(self, order_id):
        if not order_id:
            logging.error('order id is null')
            return None

        try:
            return self._cancel_order(order_id)
        except Exception as e:
            logging.error('%s %s except: %s' % (self.name, get_current_function_name(), e))

            return None

    def get_orders(self, order_ids):
        try:
            return self._get_orders(order_ids)
        except Exception as e:
            logging.error('%s %s except: %s' % (self.name, get_current_function_name(), e))
            return None

    def get_orders_history(self):
        try:
            return self._get_orders_history()
        except Exception as e:
            logging.error('%s %s except: %s' % (self.name, get_current_function_name(), e))
            return None

    def get_balances(self):
        try:
            res = self._get_balances()
        except Exception as e:
            logging.error('%s %s except: %s' % (self.name, get_current_function_name(), e))
            return None
        return res

    def cancel_all(self):
        try:
            res = self._cancel_all()
        except Exception as e:
            logging.error('%s %s except: %s' % (self.name, get_current_function_name(), e))
            return None
        return res

    def _buy_limit(self, amount, price):
        raise NotImplementedError("%s.buy(self, amount, price)" % self.name)

    def _sell_limit(self, amount, price):
        raise NotImplementedError("%s.sell(self, amount, price)" % self.name)

    def _buy_maker(self, amount, price):
        raise NotImplementedError("%s.buy_maker(self, amount, price)" % self.name)

    def _sell_maker(self, amount, price):
        raise NotImplementedError("%s.sell_maker(self, amount, price)" % self.name)

    def _get_order(self, order_id):
        raise NotImplementedError("%s.get_order(self, order_id)" % self.name)

    def _cancel_order(self, order_id):
        raise NotImplementedError("%s.cancel_order(self, order_id)" % self.name)

    def _get_orders(self, order_ids):
        raise NotImplementedError("%s.get_orders(self, order_ids)" % self.name)

    def _get_orders_history(self):
        raise NotImplementedError("%s._get_orders_history(self)" % self.name)

    def _cancel_all(self):
        raise NotImplementedError("%s.cancel_all(self)" % self.name)

    def deposit(self):
        raise NotImplementedError("%s.deposit(self)" % self.name)

    def withdraw(self, amount, address):
        raise NotImplementedError("%s.withdraw(self, amount, address)" % self.name)

    def _get_balances(self):
        raise NotImplementedError("%s.get_balances(self)" % self.name)

    def test(self):
        return None
