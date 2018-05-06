import logging
import json
import time
import os
import math
import os, time
import sys
import traceback
import zmq
import socket

class Push:
    def __init__(self, zmq_port, zmq_host=None):
        self.zmq_port = zmq_port
        self.zmq_host = zmq_host
        self.is_terminated = False
        self.publisher = None
        self.subscriber = None

    def terminate(self):
        self.is_terminated = True

    def process_message(self,message):
        pass

    def start_publish_server(self):
        import zmq
        import time
        context = zmq.Context()
        self.publisher = context.socket(zmq.ZMQ_PUB)
        self.publisher.bind("tcp://*:%s"%self.zmq_port)
        
        logging.info("zmq msg_server start...")
        while not self.is_terminated:
            # Wait for next request from client
            message = socket.recv()
            logging.info("new pull message: %s", message)
            self.process_message(message)

            time.sleep (1) # Do some 'work'

    def publish_msg_obj(self, pyObj):
        import zmq
        try:
            message = json.dumps(pyObj)
            logging.info( "notify message %s", message)

            self.publisher.send_string(message)
        except Exception as e:
            logging.warning("publish_msg_obj Exception", exc_info=True)
            pass

    def publish_msg(self, type, price):
        message = {'type':type, 'price':price}
        self.publish_msg_obj(message)

    def subscribe_msg(self, topics=None):
        context = zmq.Context()
        self.subscriber = context.socket(zmq.SUB)

        self.subscriber.connect ("tcp://%s:%s" % (self.zmq_host, self.zmq_port))
  
        # manage subscriptions  
        if not topics:  
            print("Receiving messages on ALL topics...")
            self.subscriber.setsockopt(zmq.SUBSCRIBE,'')  
        else:  
            print("Receiving messages on topics: %s ..." % topics)  
            for t in topics:  
                self.subscriber.setsockopt(zmq.SUBSCRIBE,t)  

        try:  
            while True:  
                #topic, msg = s.recv_multipart()  
                topic, msg = self.subscriber.recv_pyobj()
                print('   Topic: %s, msg:%s' % (topic, msg)) 
        except KeyboardInterrupt:  
            pass  
        print("Done.")