import json
import time
import os
import sys
import traceback
import logging
import xrypto.config as config

from xrypto.observers.basicbot import BasicBot, ratelimit
from xrypto.brokers.broker_factory import create_brokers

class BalanceDumper(BasicBot):
    bch_product = 'Bitfinex_BCH_BTC'
    eth_product = 'Bitfinex_ETH_BTC'

    last_profit = 0
    tick_wait = 10*1

    out_dir = './data/'
    asset_csv = 'asset_eth.csv'

    def __init__(self):        
        self.brokers = create_brokers(
            ['KKEX_BCH_BTC', 'Bitfinex_BCH_BTC'])

        self.btc_balance = 0
        self.bch_balance = 0
        self.eth_balance = 0

        self.init_btc = config.init_kk_btc + config.init_bf_btc
        self.init_bch = config.init_kk_bch + config.init_bf_bch
        self.init_eth = config.init_kk_eth + config.init_bf_eth

        self.first_run = True
        try:
            os.mkdir(self.out_dir)
        except:
            pass

        logger = logging.getLogger()    # initialize logging class
        logger.setLevel(logging.INFO)  # default log level

    def save_asset(self, price, btc, bch, eth, profit):
        filename = self.out_dir + self.asset_csv
        need_header = False

        if not os.path.exists(filename):
            need_header = True

        fp = open(filename, 'a+')

        timestr = time.strftime("%d/%m/%Y %H:%M:%S")

        if need_header:
            fp.write("timestamp, timestr, price, btc, bch, eth, profit\n")
        line = "%d, %s, %.f, %.2f, %.2f, %.2f, %.2f\n" % (time.time(), timestr, price, btc, bch, eth, profit)
        fp.write(line)
        fp.close()

    def sum_balance(self):
        self.btc_balance = self.bch_balance = self.eth_balance = 0
        for kclient in self.brokers:
            self.btc_balance += self.brokers[kclient].btc_balance
            self.bch_balance += self.brokers[kclient].bch_balance 
            self.eth_balance += self.brokers[kclient].eth_balance

    @ratelimit
    def tick(self, depths):
        # get&verify price
        try:
            bch_bid_price = depths[self.bch_product]["bids"][0]['price']
            bch_ask_price = depths[self.bch_product]["asks"][0]['price']

            if bch_bid_price == 0 or bch_ask_price == 0:
                logging.warn("exception  bch ticker")
                return

            eth_bid_price = depths[self.eth_product]["bids"][0]['price']
            eth_ask_price = depths[self.eth_product]["asks"][0]['price']

            if eth_bid_price == 0 or eth_ask_price == 0:
                logging.warn("exception eth ticker")
                return
        except  Exception as ex:
            logging.warn("exception depths:%s" % ex)
            traceback.print_exc()
            return

        # Update client balance
        self.update_balance()
        self.sum_balance()
        
        btc_diff = self.btc_balance - self.init_btc
        bch_diff = self.bch_balance - self.init_bch
        eth_diff = self.eth_balance - self.init_eth

        btc_profit = bch_diff * bch_bid_price + btc_diff

        logging.info('btc_profit:%.4f, btc_diff:%.4f, bch_diff: %.2f, eth_diff: %.2f',
                     btc_profit, btc_diff, bch_diff, eth_diff)

        if (self.first_run or abs(btc_profit - self.last_profit) > 0.01):
            self.first_run = False
            self.last_profit = btc_profit
            self.save_asset(bch_bid_price,
                            self.btc_balance, 
                            self.bch_balance, 
                            self.eth_balance,
                            btc_profit)
            self.render_to_html()

    def render_to_html(self):
        import pandas as pd
        from pyecharts import Line

        df = pd.read_csv(self.out_dir + self.asset_csv)

        attr = [i[1] for i in df.values]
        price = [i[2] for i in df.values]
        btc = [i[3] for i in df.values]
        bch = [i[4] for i in df.values]
        eth = [i[5] for i in df.values]
        profit = [i[6] for i in df.values]

        line = Line("利润曲线")
        line.add("profit", attr, profit, is_smooth=True, mark_point=["max","average","min"], mark_line=["max", "average","min"])
        # line.add("外盘内盘价差", attr2, v2, is_smooth=True, mark_line=["max", "average"])
        line.render('./data/kp.html')

        line = Line("资产统计")
        line.add("btc", attr, btc)
        line.add("bch", attr, bch)
        line.add("eth", attr, eth)

        line.render('./data/ka.html')


if __name__ == "__main__":
    cli = BalanceDumper()
    cli.main(config)

