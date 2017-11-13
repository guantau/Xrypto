import logging
import json
import time
import os
import math
import sys
import traceback
from xrypto.observers.observer import Observer

class BasicBot(Observer):
    tick_wait = 3
    last_tick = 0
    def __init__(self):
        super().__init__()

        self.orders = []

        logging.info('BasicBot Setup complete')

    def new_order(self, market, type, maker_only=False, amount=None, price=None):
        if type == 'buy' or type == 'sell':
            if not price or not amount:
                print(price)
                print(amount)
                assert(False)

            if maker_only:                
                if type == 'buy':
                    order_id = self.brokers[market].buy_maker(amount, price)
                else:
                    order_id = self.brokers[market].sell_maker(amount, price)
            else:
                if type == 'buy':
                    order_id = self.brokers[market].buy_limit(amount, price)
                else:
                    order_id = self.brokers[market].sell_limit(amount, price)

            if not order_id or order_id == -1:
                logging.warn("%s @%s %f/%f failed, order_id = %s" %
                             (type, market, amount, price, order_id))
                return None
    

            order = {
                'market': market, 
                'order_id': order_id,
                'price': price,
                'amount': amount,
                'deal_amount':0,
                'deal_index': 0, 
                'type': type,
                'time': time.time()
            }
            self.orders.append(order)
            logging.verbose("submit order %s" % (order))

            return order

        return None


    def remove_order(self, order_id):
        self.orders = [x for x in self.orders if not x['order_id'] == order_id]

    def get_order(self, order_id):
        for x in self.orders:
            if x['order_id'] == order_id:
                return x

    def get_orders(self, type):
        orders_snapshot = [x for x in self.orders if x['type'] == type]
        return orders_snapshot

    def get_order_ids(self):
        order_ids = [x['order_id'] for x in self.orders]
        return order_ids

    def selling_len(self):
        return len(self.get_orders('sell'))

    def buying_len(self):
        return len(self.get_orders('buy'))

    def is_selling(self):
        return len(self.get_orders('sell')) > 0

    def is_buying(self):
        return len(self.get_orders('buy')) > 0

    def get_sell_price(self):
        return self.sprice

    def get_buy_price(self):
        return self.bprice

    def get_spread(self):
        return self.sprice - self.bprice
        
    def cancel_order(self, market, type, order_id):
        result = self.brokers[market].cancel_order(order_id)
        if not result:
            logging.warn("cancel %s #%s failed" % (type, order_id))
            return False
        else:
            logging.info("cancel %s #%s ok" % (type, order_id))
            return True

    def cancel_all_orders(self, market):
        orders = self.brokers[market].get_orders_history()
        if not orders:
            return

        for order in orders:
            logging.verbose("Cancelling: %s %s @ %s" % (order['type'], order['amount'], order['price']))
            while True:
                result = self.cancel_order(market, order['type'], order['order_id']); 
                if not result:
                    time.sleep(10) 
                else:
                    break

    def cancel_local_orders(self, market):
        orders = self.brokers[market].get_orders_history()
        if not orders:
            return

        for order in orders:
            logging.verbose("Cancelling: %s %s @ %s" % (order['type'], order['amount'], order['price']))
            while True:
                result = self.cancel_order(market, order['type'], order['order_id']); 
                if not result:
                    time.sleep(10) 
                else:
                    break

    def update_balance(self):
        for kclient in self.brokers:
            self.brokers[kclient].get_balances()

def ratelimit(func):
    def __decorator(self, depths):
        current_time = time.time()
        if current_time - self.last_tick < self.tick_wait:
            return
        self.last_tick = current_time

        func(self, depths)
    return __decorator
