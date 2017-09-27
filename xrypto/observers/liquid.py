import logging
from .observer import Observer
import json
import time
import os
import random
import sys
import traceback
import config
from .basicbot import BasicBot
import threading
from brokers.broker_factory import create_brokers

class Liquid(BasicBot):
    def __init__(self, mm_market='KKEX_BCH_BTC', 
                        refer_markets=['Bitfinex_BCH_BTC'],
                        hedge_market='Bitfinex_BCH_BTC'):
        super().__init__()

        self.mm_market = mm_market
        self.refer_markets = refer_markets
        self.hedge_market = hedge_market

        self.data_lost_count = 0
        self.risk_protect_count = 10

        self.slappage = 0.005
        self.brokers = create_brokers([mm_market, hedge_market])

        self.mm_broker = self.brokers[mm_market]
        self.hedge_broker = self.brokers[hedge_market]

        self.cancel_all_orders(self.mm_market)

        logging.info('MarketMaker Setup complete')
        # time.sleep(2)

    def terminate(self):
        super().terminate()
        
        self.cancel_all_orders(self.mm_market)

        logging.info('terminate complete')

    def risk_protect(self):
        self.data_lost_count+=1
        if self.data_lost_count > self.risk_protect_count:
            logging.warn('risk protect~stop liquid supplly. %s' % self.data_lost_count)

            self.cancel_all_orders(self.mm_market)
            self.data_lost_count = 0

    def tick(self, depths):
        refer_market = None
        for m in self.refer_markets:
            try:
                refer_bid_price, refer_ask_price = self.get_ticker(depths, m)
                refer_market = m
                break
            except Exception as e:
                logging.warn('%s exception when get_ticker:%s' % (m, e))
                continue
        
        if not refer_market:
            logging.warn('no avaliable market depths')
            self.risk_protect()
            return
        
        if self.hedge_market:
            try:
                self.hedge_bid_price, self.hedge_ask_price = self.get_ticker(depths, self.hedge_market)
            except Exception as e:
                logging.warn('%s exception when get_ticker:%s' % (self.hedge_market, e))
                self.risk_protect()
                return
        
        self.check_orders(depths, refer_bid_price, refer_ask_price)

        self.place_orders(refer_bid_price, refer_ask_price)

    def get_ticker(self, depths, market):
        bid_price = depths[market]["bids"][0]['price']
        ask_price = depths[market]["asks"][0]['price']

        # logging.debug("market:%s bid, ask=(%s/%s)" % (market, bid_price, ask_price))
        return bid_price, ask_price

    def place_orders(self, refer_bid_price, refer_ask_price):
        # Update client balance
        self.update_balance()   

        max_bch_trade_amount = config.LIQUID_MAX_BCH_AMOUNT
        min_bch_trade_amount = config.LIQUID_MIN_BCH_AMOUNT

        liquid_max_diff = config.LIQUID_MAX_DIFF

        # excute trade
        if self.buying_len() < config.LIQUID_BUY_ORDER_PAIRS:
            bprice = refer_bid_price*(1-config.LIQUID_INIT_DIFF)

            amount = round(max_bch_trade_amount*random.random(), 2)
            price = round(bprice*(1 - liquid_max_diff*random.random()), 5) #-10% random price base on sprice

            Qty = min(self.mm_broker.btc_balance/price, self.hedge_broker.bch_available)
            # Qty = min(Qty, config.LIQUID_BTC_RESERVE/price)

            if Qty < amount or amount < min_bch_trade_amount:
                logging.verbose("BUY amount (%s) not IN (%s, %s)" % (amount, min_bch_trade_amount, Qty))
            else:
                self.new_order(self.mm_market, 'buy', amount=amount, price=price)

        if self.selling_len() < config.LIQUID_SELL_ORDER_PAIRS:
            sprice = refer_ask_price*(1+config.LIQUID_INIT_DIFF)

            amount = round(max_bch_trade_amount*random.random(), 2)
            price = round(sprice*(1 + liquid_max_diff*random.random()), 5) # +10% random price base on sprice

            Qty = min(self.mm_broker.bch_available, self.hedge_broker.btc_available/price)
            # Qty = min(Qty, config.LIQUID_BCH_RESERVE)
            if Qty < amount or amount < min_bch_trade_amount:
                logging.verbose("SELL amount (%s) not IN (%s, %s)" % (amount, min_bch_trade_amount, Qty))
            else:
                self.new_order(self.mm_market, 'sell', amount=amount, price=price)

        return

    def check_orders(self, depths, refer_bid_price, refer_ask_price):
        max_bprice = refer_bid_price*(1-config.LIQUID_MIN_DIFF)
        min_sprice = refer_ask_price*(1+config.LIQUID_MIN_DIFF)
        
        order_ids = self.get_order_ids()
        if not order_ids:
            return
        
        orders = self.mm_broker.get_orders(order_ids)
        if orders is not None:
            for order in orders:
                local_order = self.get_order(order['order_id'])
                self.hedge_order(local_order, order)

                if order['status'] == 'CLOSE' or order['status'] == 'CANCELED':
                    logging.info("order#%s %s: amount = %s price = %s deal = %s" % (order['order_id'], order['status'], order['amount'], order['price'], order['deal_amount']))
                    self.remove_order(order['order_id'])

                if order['type'] =='buy':
                    current_time = time.time()
                    if order['price'] > max_bprice:
                        logging.info("[TraderBot] cancel last BUY trade " +
                                        "occured %.2f seconds ago" %
                                        (current_time - local_order['time']))
                        logging.info("cancel max_bprice %s order['price'] = %s" % (max_bprice, order['price']))

                        self.cancel_order(self.mm_market, 'buy', order['order_id'])
                elif order['type'] == 'sell':
                    current_time = time.time()
                    if order['price'] < min_sprice:
                        logging.info("[TraderBot] cancel last SELL trade " +
                                        "occured %.2f seconds ago" %
                                        (current_time - local_order['time']))
                        logging.info("cancel min_sprice %s order['price'] = %s" % (min_sprice, order['price']))

                        self.cancel_order(self.mm_market, 'sell', order['order_id'])
        
    def hedge_order(self, order, result):
        if result['deal_amount'] <= config.LIQUID_HEDGE_MIN_AMOUNT:
            return

        amount = result['deal_amount'] - order['deal_amount']
        if amount <= config.LIQUID_HEDGE_MIN_AMOUNT:
            logging.debug("[hedger]deal nothing while. v:%s <= min:%s", amount, config.LIQUID_HEDGE_MIN_AMOUNT)
            return

        order_id = result['order_id']        
        deal_amount = result['deal_amount']
        price = result['avg_price']

        client_id = str(order_id) + '-' + str(order['deal_index'])

        logging.info("order # %s new deal: %s", order_id, result)
        hedge_side = 'sell' if order['type'] =='buy' else 'buy'
        logging.info('hedge [%s] to %s: %s %s %s', client_id, self.hedge_market, hedge_side, amount, price)

        if hedge_side == 'sell':
            self.brokers[self.hedge_market].sell_limit(amount, self.hedge_bid_price*(1-self.slappage))
        else:
            self.brokers[self.hedge_market].buy_limit(amount, self.hedge_ask_price*(1+self.slappage))

        # update the deal_amount of local order
        self.remove_order(order_id)
        order['deal_amount'] = deal_amount
        order['deal_index'] +=1
        self.orders.append(order)