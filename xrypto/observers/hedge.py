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

class Hedge(BasicBot):
    def __init__(self, currency, mm_market, 
                        refer_markets,
                        hedge_market,
                        max_trade_amount,
                        min_trade_amount):
        super().__init__()

        assert(currency)
        assert(mm_market)
        assert(refer_markets)
        assert(hedge_market)
        assert(max_trade_amount)
        assert(min_trade_amount)

        self.currency = currency
        self.mm_market = mm_market
        self.refer_markets = refer_markets
        self.hedge_market = hedge_market
        self.max_trade_amount = max_trade_amount
        self.min_trade_amount = min_trade_amount

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
        
        try:
            mm_bid_price, mm_ask_price = self.get_ticker(depths, self.mm_market)
        except Exception as e:
            logging.warn('%s exception when get_ticker:%s' % (self.mm_market, e))
            return
        
        self.check_orders(refer_bid_price, refer_ask_price)

        self.place_orders(refer_bid_price, refer_ask_price, mm_bid_price, mm_ask_price)

    def get_ticker(self, depths, market):
        bid_price = depths[market]["bids"][0]['price']
        ask_price = depths[market]["asks"][0]['price']

        # logging.debug("market:%s bid, ask=(%s/%s)" % (market, bid_price, ask_price))
        return bid_price, ask_price

    def place_orders(self, refer_bid_price, refer_ask_price, mm_bid_price, mm_ask_price):
        # Update client balance
        if self.buying_len() < 2*config.LIQUID_BUY_ORDER_PAIRS or self.selling_len() < 2 * config.LIQUID_SELL_ORDER_PAIRS:
            self.update_balance() 

        liquid_max_diff = config.LIQUID_MAX_DIFF

        # excute trade
        if self.buying_len() < 2*config.LIQUID_BUY_ORDER_PAIRS:
            bprice = refer_bid_price*(1-config.LIQUID_INIT_DIFF)

            amount = round(self.max_trade_amount * random.random(), 2)
            price = round(bprice*(1 - liquid_max_diff*random.random()), 5) #-10% random price base on bprice

            Qty = min(self.mm_broker.availabe.get('BTC', 0) / price,
                      self.hedge_broker.available.get(self.currency, 0))

            if Qty < amount or amount < self.min_trade_amount:
                logging.verbose("BUY amount (%s) not IN (%s, %s)" %
                                (amount, self.min_trade_amount, Qty))
            else:
                if mm_ask_price > 0 and mm_ask_price < bprice:
                    price = bprice
                    
                if (mm_ask_price > 0 and mm_ask_price < bprice) or self.buying_len() < config.LIQUID_BUY_ORDER_PAIRS:
                    self.new_order(self.mm_market, 'buy', amount=amount, price=price)

        if self.selling_len() < 2*config.LIQUID_SELL_ORDER_PAIRS:
            sprice = refer_ask_price*(1+config.LIQUID_INIT_DIFF)

            amount = round(self.max_trade_amount * random.random(), 2)
            price = round(sprice*(1 + liquid_max_diff*random.random()), 5) # +10% random price base on sprice

            Qty = min(self.mm_broker.available.get(self.currency, 0),
                      self.hedge_broker.availabe.get('BTC', 0) / price)

            if Qty < amount or amount < self.min_trade_amount:
                logging.verbose("SELL amount (%s) not IN (%s, %s)" %
                                (amount, self.min_trade_amount, Qty))
            else:
                if mm_bid_price > 0 and mm_bid_price > sprice:
                    price = sprice

                if (mm_bid_price > 0 and mm_bid_price > sprice) or self.selling_len() < config.LIQUID_SELL_ORDER_PAIRS:
                    self.new_order(self.mm_market, 'sell', amount=amount, price=price)


        return

    def check_orders(self, refer_bid_price, refer_ask_price):
        max_bprice = round(refer_bid_price * (1 - config.LIQUID_MIN_DIFF), 5)
        min_bprice = round(refer_bid_price*(1-config.LIQUID_MAX_DIFF), 5)

        min_sprice = round(refer_ask_price*(1+config.LIQUID_MIN_DIFF), 5)
        max_sprice = round(refer_ask_price * (1 + config.LIQUID_MAX_DIFF), 5)

        order_ids = self.get_order_ids()
        if not order_ids:
            return
        
        orders = self.mm_broker.get_orders(order_ids)
        if orders is not None:
            for order in orders:
                local_order = self.get_order(order['order_id'])
                self.hedge_order(local_order, order)
                timediff = int(time.time() - local_order['time'])
                timeout_adjust = random.randint(60, 600)
                
                if order['status'] == 'CLOSE' or order['status'] == 'CANCELED':
                    logging.info("order#%s %s: amount = %s price = %s deal = %s" % (order['order_id'], order['status'], order['amount'], order['price'], order['deal_amount']))
                    self.remove_order(order['order_id'])

                if order['type'] =='buy':
                    if order['price'] > max_bprice or (order['price'] < min_bprice and timediff > timeout_adjust):
                        logging.info("[TraderBot] cancel BUY  order #%s ['price'] = %s NOT IN [%s, %s] or timeout[%s>%s]" % (order['order_id'], order['price'], min_bprice, max_bprice, timediff, timeout_adjust))

                        self.cancel_order(self.mm_market, 'buy', order['order_id'])
                elif order['type'] == 'sell':
                    if order['price'] < min_sprice or (order['price'] > max_sprice and timediff > timeout_adjust):
                        logging.info("[TraderBot] cancel SELL order #%s ['price'] = %s NOT IN [%s, %s] or timeout[%s>%s]" % (order['order_id'], order['price'], min_sprice, max_sprice, timediff, timeout_adjust))

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
