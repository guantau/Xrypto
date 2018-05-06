#-*- coding: utf-8 -*-

# Copyright (C) 2016-2017, Phil Song <songbohr@gmail.com>

import markets
import observers
import config
import time
import logging
import json
from concurrent.futures import ThreadPoolExecutor, wait
import traceback

import re,sys,re
import string
from datafeed import Datafeed

class Arbitrer(Datafeed):
    def __init__(self):
        super.__init__()
                
    def get_profit_for(self, mi, mj, kask, kbid):
        if self.depths[kask]["asks"][mi]["price"] >= self.depths[kbid]["bids"][mj]["price"]:
            return 0, 0, 0, 0

        max_amount_buy = 0
        for i in range(mi + 1):
            max_amount_buy += self.depths[kask]["asks"][i]["amount"]

        max_amount_sell = 0
        for j in range(mj + 1):
            max_amount_sell += self.depths[kbid]["bids"][j]["amount"]

        max_amount_pair_t = min(max_amount_buy, max_amount_sell)

        buy_total = 0
        w_bprice = 0
        for i in range(mi + 1):
            price = self.depths[kask]["asks"][i]["price"]
            amount = min(max_amount_pair_t, buy_total + self.depths[kask]["asks"][i]["amount"]) - buy_total

            buy_total += amount

            if w_bprice == 0 or buy_total == 0:
                w_bprice = price
            else:
                w_bprice = (w_bprice * (buy_total - amount) + price * amount) / buy_total
            
            if max_amount_pair_t - buy_total <= 0.000001:
                break

        sell_total = 0
        w_sprice = 0
        for j in range(mj + 1):
            price = self.depths[kbid]["bids"][j]["price"]
            amount = min(max_amount_pair_t, sell_total + self.depths[kbid]["bids"][j]["amount"]) - sell_total

            sell_total += amount

            if w_sprice == 0 or sell_total == 0:
                w_sprice = price
            else:
                w_sprice = (w_sprice * (sell_total - amount) + price * amount) / sell_total
        
            if max_amount_pair_t - sell_total <= 0.000001:
                break

        # sell should == buy
        if abs(sell_total-buy_total) > 0.000001:
            logging.warn("sell_total=%s, buy_total=%s, max_amount_pair_t=%s", 
                sell_total, buy_total, max_amount_pair_t)
            return 0, 0, 0, 0

        volume = buy_total # or sell_total

        profit = sell_total * w_sprice - buy_total * w_bprice
        return profit, volume, w_bprice, w_sprice

    def get_max_depth(self, kask, kbid):
        i = 0
        if len(self.depths[kbid]["bids"]) != 0 and \
           len(self.depths[kask]["asks"]) != 0:
            while self.depths[kask]["asks"][i]["price"] \
                  < self.depths[kbid]["bids"][0]["price"]:
                if i >= len(self.depths[kask]["asks"]) - 1:
                    break
                # logging.debug("i:%s,%s/%s,%s/%s", i, kask, self.depths[kask]["asks"][i]["price"],
                #   kbid, self.depths[kbid]["bids"][0]["price"])

                i += 1

        j = 0
        if len(self.depths[kask]["asks"]) != 0 and \
           len(self.depths[kbid]["bids"]) != 0:
            while self.depths[kask]["asks"][0]["price"] \
                  < self.depths[kbid]["bids"][j]["price"]:
                if j >= len(self.depths[kbid]["bids"]) - 1:
                    break
                # logging.debug("j:%s,%s/%s,%s/%s", j, kask, self.depths[kask]["asks"][0]["price"],
                #     kbid, self.depths[kbid]["bids"][j]["price"])

                j += 1

        return i, j

    def arbitrage_depth_opportunity(self, kask, kbid):
        best_profit, best_volume = (0, 0)
        best_i, best_j = (0, 0)
        best_w_bprice, best_w_sprice = (0, 0)

        maxi, maxj = self.get_max_depth(kask, kbid)
        for i in range(maxi + 1):
            for j in range(maxj + 1):
                profit, volume, w_bprice, w_sprice = self.get_profit_for(
                    i, j, kask, kbid)
                if profit >= 0 and profit >= best_profit:
                    best_profit = profit
                    best_volume = volume
                    best_i, best_j = (i, j)
                    best_w_bprice, best_w_sprice = (
                        w_bprice, w_sprice)
        return best_profit, best_volume, \
               self.depths[kask]["asks"][best_i]["price"], \
               self.depths[kbid]["bids"][best_j]["price"], \
               best_w_bprice, best_w_sprice

    def arbitrage_opportunity(self, kask, ask, kbid, bid):
        profit, volume, exe_bprice, exe_sprice, w_bprice,\
            w_sprice = self.arbitrage_depth_opportunity(kask, kbid)

        if volume == 0 or exe_bprice == 0 or exe_sprice == 0:
            logging.warn("parameter exception %s %s %s" % (volume, exe_bprice, exe_sprice))
            return

        ask_market = self.get_market(kask)
        bid_market = self.get_market(kbid)
        if round(w_sprice * ask_market.fee_rate * config.Diff, 8)  >= round(w_bprice * bid_market.fee_rate, 8):
            logging.verbose("weight pricediff_exist check failed: %s > %s" % (
                round(w_sprice * ask_market.fee_rate * config.Diff, 8), round(w_bprice * bid_market.fee_rate, 8)))
            return

        fee_rate = max(ask_market.fee_rate, bid_market.fee_rate)
        profit = round(profit*(1-fee_rate), 8)

        w_perc = round((w_sprice - w_bprice) / w_bprice - fee_rate, 4)

        # notify observer
        for observer in self.observers:
            observer.opportunity(
                profit, volume, exe_bprice, kask, exe_sprice, kbid,
                w_perc, w_bprice, w_sprice,
                base_currency=ask_market.base_currency, 
                market_currency=ask_market.market_currency)

    def is_pair_market(self, kmarket1, kmarket2):
        if kmarket1 == kmarket2:  # same market
            return False

        market1 = self.get_market(kmarket1)
        if not market1:
            return False

        market2 = self.get_market(kmarket2)
        if not market2:
            return False

        if market1.base_currency != market2.base_currency:
            return False

        if market1.market_currency != market2.market_currency:
            return False 

        return True

    def pricediff_exist(self, depth1, depth2):
        if not depth1 or not depth2:
            return False
        if not depth1["asks"] or not depth2["bids"]:
            return False
        if len(depth1["asks"]) <= 0 or len(depth2["bids"]) <= 0:
            return False
        
        sprice = float(depth1["asks"][0]['price'])
        bprice = float(depth2["bids"][0]['price'])

        if sprice >= bprice:
            logging.debug("orderbook pricediff_exist check failed: %s > %s" % (
                round(sprice * config.FEE * config.Diff, 8), round(bprice * config.FEE, 8)))
            return False   

        if round(sprice * config.FEE * config.Diff, 8)  >= round(bprice * config.FEE, 8):
            logging.verbose("FEE*DIFF pricediff_exist check failed: %s > %s" % (
                round(sprice * config.FEE * config.Diff, 8), round(bprice * config.FEE, 8)))
            return False
        
        return True

    def observer_tick(self):
        # super.observer_tick()
        
        for observer in self.observers:
            observer.begin_opportunity_finder(self.depths)

        for kmarket1 in self.depths:
            for kmarket2 in self.depths:
                if not self.is_pair_market(kmarket1, kmarket2):  # same market
                    continue

                logging.debug("detect ask < bid in [%s %s]" % (kmarket1, kmarket2))

                depth1 = self.depths[kmarket1]
                depth2 = self.depths[kmarket2]

                if not self.pricediff_exist(depth1, depth2):
                    continue

                logging.debug("price diff exist in [%s %s]" % (kmarket1, kmarket2))

                self.arbitrage_opportunity(kmarket1, depth1["asks"][0],
                                           kmarket2, depth2["bids"][0])

        for observer in self.observers:
            observer.end_opportunity_finder()

