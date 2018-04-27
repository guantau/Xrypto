import abc
import json
import logging

class Observer(object, metaclass=abc.ABCMeta):
    def __init__(self):
        self.is_terminated = False

    def terminate(self):
        self.is_terminated = True
    
    def tick(self, depths):
        pass
        
    def begin_opportunity_finder(self, depths):
        pass

    def end_opportunity_finder(self):
        pass

    ## abstract
    # @abc.abstractmethod
    def opportunity(self, profit, volume, bprice, kask, sprice, kbid, perc, 
                        w_bprice, w_sprice, 
                        base_currency="CNY", market_currency="BTC"):
        pass

    def main(self, config):
        from kafka import KafkaConsumer
        kafka_topic = config.kafka_topic
        bootstrap_servers = config.bootstrap_servers
        try:
            consumer = KafkaConsumer(kafka_topic,
                                 value_deserializer=lambda m: json.loads(
                                     m.decode('utf-8')),
                                 bootstrap_servers=bootstrap_servers)
            for message in consumer:
                # print (message)
                # message value and key are raw bytes -- decode if necessary!
                # e.g., for unicode: `message.value.decode('utf-8')`
                logging.info ("observer: %s:%d:%d: key=%s" % (message.topic, message.partition,
                                             message.offset, message.key))

                depths = message.value
                self.tick(depths)
        except Exception as ex:
            logging.warn("exception depths:%s" % ex)
            traceback.print_exc()

