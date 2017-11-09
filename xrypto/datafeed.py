#-*- coding: utf-8 -*-

# Copyright (C) 2017, Phil Song <songbohr@gmail.com>

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
import signal

from kafka import KafkaProducer
from kafka import KafkaConsumer
from kafka.errors import KafkaError

from markets.market_factory import create_markets

is_sigint_up = False

def sigint_handler(signum, frame):
    global is_sigint_up
    is_sigint_up = True
    print ('catched interrupt signal!')

class Datafeed(object):
    def __init__(self):
        self.markets = []
        self.observers = []
        self.depths = {}
        self.init_markets(config.markets)
        self.init_observers(config.observers)
        self.threadpool = ThreadPoolExecutor(max_workers=10)

    def init_markets(self, _markets):
        logging.debug("init_markets:%s" % _markets)
        self.market_names = _markets
        markets = create_markets(_markets)

        for market_name, market in markets.items():
            if self.get_market(market_name):
                continue
            self.markets.append(market)

    def init_observers(self, _observers):
        logging.debug("init_observers:%s" % _observers)

        self.observer_names = _observers
        for observer_name in _observers:
            try:
                exec('import observers.' + observer_name.lower())
                observer = eval('observers.' + observer_name.lower() + '.' +
                                observer_name + '()')
                self.observers.append(observer)
            except (ImportError, AttributeError) as e:
                print("%s observer name is invalid: Ignored (you should check your config file)" % (observer_name))
                print(e)

    def register_observer(self, _observer):
        logging.debug("register_observer:%s" % _observer)
        self.observers.append(_observer)


    def get_market(self, market_name):
        for market in self.markets:
            if market.name == market_name:
                return market

        return None


    def observer_tick(self):
        for observer in self.observers:
            observer.tick(self.depths)

    def tick(self):
        self.print_tickers()
 
        self.observer_tick()

    def __get_market_depth(self, market, depths):
        depth = market.get_depth()
        if depth:
            depths[market.name] = depth

    def update_depths(self):
        depths = {}
        futures = []

        for market in self.markets:
            futures.append(self.threadpool.submit(self.__get_market_depth,
                                                  market, depths))
        wait(futures, timeout=20)
        return depths

    def print_tickers(self):
        for market in self.markets:
            logging.debug("ticker: " + market.name + " - " + str(market.get_ticker()))

    def replay_history(self, directory):
        import os
        import json
        import pprint
        files = os.listdir(directory)
        files.sort()
        for f in files:
            depths = json.load(open(directory + '/' + f, 'r'))
            self.depths = {}
            for market in self.market_names:
                if market in depths:
                    self.depths[market] = depths[market]
            self.tick()

    def update_balance(self):
        pass

    def terminate(self):
        for observer in self.observers:
            observer.terminate()

        for market in self.markets:
            market.terminate()

    def _run_loop(self, is_feed = True):
        if not is_feed and len(self.observers) == 0:
            print('empty observers')
            return

        if is_feed and len(self.markets) == 0:
            print('empty markets')
            return
        #
        signal.signal(signal.SIGINT, sigint_handler)
        #以下那句在windows python2.4不通过,但在freebsd下通过
        signal.signal(signal.SIGHUP, sigint_handler)
        signal.signal(signal.SIGTERM, sigint_handler)

        kafka_topic = config.kafka_topic
        bootstrap_servers = config.bootstrap_servers
        print(bootstrap_servers)

        try:
            if is_feed:
                producer = KafkaProducer(bootstrap_servers=bootstrap_servers,
                                            # key_serializer=str.encode,
                                            value_serializer=lambda v: json.dumps(v).encode('utf-8'))
            else:
                consumer = KafkaConsumer(kafka_topic,
                                    value_deserializer=lambda m: json.loads(
                                        m.decode('utf-8')),
                                        bootstrap_servers=bootstrap_servers)
        except Exception as ex:
            logging.warn("exception depths:%s" % ex)
            traceback.print_exc()
            return

        while True:
            if is_feed:
                self.depths = self.update_depths()
                print(producer)
                future = producer.send(kafka_topic, value=self.depths)
                # Block for 'synchronous' sends
                try:
                    record_metadata = future.get(timeout=60)
                    print(record_metadata)
                except  Exception as ex:
                    logging.warn("exception depths:%s" % ex)
                    traceback.print_exc()
                    continue
            else:
                for message in consumer:
                    # print (message)
                    # message value and key are raw bytes -- decode if necessary!
                    # e.g., for unicode: `message.value.decode('utf-8')`
                    print ("%s:%d:%d: key=%s" % (message.topic, message.partition,
                                                message.offset, message.key))
                    # print(message)
                    self.update_balance()

                    self.depths = message.value
                    self.tick()
                print('consumer done...')
                    
                # try:
                #     self.tick()
                # except Exception as ex:
                #     logging.warn("exception depths:%s" % ex)
                #     traceback.print_exc()
                #     return

            if is_sigint_up:
                # 中断时需要处理的代码
                logging.info("APP Exit")
                self.terminate()
                break
            sys.stdout.write(".")
            sys.stdout.flush()
            time.sleep(config.refresh_rate)

    def run_loop(self):
        is_feed = False
        self._run_loop(is_feed)

def main():
    cli = Datafeed()
    cli._run_loop()


if __name__ == "__main__":
    main()
