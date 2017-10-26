#!/usr/bin/python
# -*- coding: utf-8 -*-
#用于访问OKCOIN 现货REST API
from .HttpMD5Util import buildMySign,httpGet,httpPost

class OKCoinSpot:

    def __init__(self,apikey,secretkey, url='https://www.okcoin.cn'):
        self.__url = url
        self.__apikey = apikey
        self.__secretkey = secretkey

    """ 获取OKCOIN现货K线
        
        :param symbol required  btc_cny：比特币    
                                ltc_cny：莱特币    
                                eth_cny :以太坊     
                                etc_cny :以太经典    
                                bcc_cny :比特现金
        :param type   required  1min : 1分钟
                                3min : 3分钟
                                5min : 5分钟
                                15min : 15分钟
                                30min : 30分钟
                                1day : 1日
                                3day : 3日
                                1week : 1周
                                1hour : 1小时
                                2hour : 2小时
                                4hour : 4小时
                                6hour : 6小时
                                12hour : 12小时  

        :param size    optional 指定获取数据的条数，默认全部获取
        :param since   optional 时间戳，返回该时间戳以后的数据(例如1417536000000)，默认全部获取
        
        :return 
        [
            1417536000000,	时间戳
            2370.16,	    开
            2380,	        高
            2352,	        低
            2367.37,	    收
            17259.83	    交易量
        ]
    """
    def kline(self, symbol, type, size = None, since = None):
        KLINE_RESOURCE = "/api/v1/kline.do"
        params=[]
        params.append('symbol=%s' % symbol)
        params.append('type=%s' % type)
        if size is not None:
            params.append('size=%s' % size)
        if since is not None:
            params.append('since=%s' % since)
        return httpGet(self.__url, KLINE_RESOURCE, '&'.join(params))

    #获取OKCOIN现货行情信息
    def ticker(self,symbol = ''):
        TICKER_RESOURCE = "/api/v1/ticker.do"
        params=''
        if symbol:
            params = 'symbol=%(symbol)s' %{'symbol':symbol}
        return httpGet(self.__url,TICKER_RESOURCE,params)

    #获取OKCOIN现货市场深度信息
    def depth(self,symbol = None, size = None):
        DEPTH_RESOURCE = "/api/v1/depth.do"
        params=[]
        if symbol is not None:
            params.append('symbol=%s' % symbol)
        if size is not None:
            params.append('size=%s' % size)
        return httpGet(self.__url,DEPTH_RESOURCE,'&'.join(params)) 

    #获取OKCOIN现货历史交易信息
    def trades(self,symbol = None, since = None):
        TRADES_RESOURCE = "/api/v1/trades.do"
        params=[]
        if symbol is not None:
            params.append('symbol=%s' % symbol)
        if since is not None:
            params.append('since=%s' % since)
        return httpGet(self.__url,TRADES_RESOURCE,'&'.join(params))
    
    #获取用户现货账户信息
    def get_userinfo(self):
        USERINFO_RESOURCE = "/api/v1/userinfo.do"
        params ={}
        params['api_key'] = self.__apikey
        params['sign'] = buildMySign(params,self.__secretkey)
        return httpPost(self.__url,USERINFO_RESOURCE,params)

    #现货交易
    def trade(self,symbol,tradeType, price='',amount=''):
        TRADE_RESOURCE = "/api/v1/trade.do"
        params = {
            'api_key':self.__apikey,
            'symbol':symbol,
            'type':tradeType
        }
        if price:
            params['price'] = price
        if amount:
            params['amount'] = amount
            
        params['sign'] = buildMySign(params,self.__secretkey)
        return httpPost(self.__url,TRADE_RESOURCE,params)
    
    def buy_limit(self, symbol, amount, price):
        return self.trade(symbol, 'buy', price=price, amount=amount)

    def sell_limit(self, symbol, amount, price):
        return self.trade(symbol, 'sell', price=price, amount=amount)


    #现货批量下单
    def batchTrade(self,symbol,tradeType,orders_data):
        BATCH_TRADE_RESOURCE = "/api/v1/batch_trade.do"
        params = {
            'api_key':self.__apikey,
            'symbol':symbol,
            'type':tradeType,
            'orders_data':orders_data
        }
        params['sign'] = buildMySign(params,self.__secretkey)
        return httpPost(self.__url,BATCH_TRADE_RESOURCE,params)

    #现货取消订单
    def cancel_order(self,symbol,orderId):
        CANCEL_ORDER_RESOURCE = "/api/v1/cancel_order.do"
        params = {
             'api_key':self.__apikey,
             'symbol':symbol,
             'order_id':orderId
        }
        params['sign'] = buildMySign(params,self.__secretkey)
        return httpPost(self.__url,CANCEL_ORDER_RESOURCE,params)

    #现货订单信息查询
    def order_info(self,symbol,orderId):
         ORDER_INFO_RESOURCE = "/api/v1/order_info.do"
         params = {
             'api_key':self.__apikey,
             'symbol':symbol,
             'order_id':orderId
         }
         params['sign'] = buildMySign(params,self.__secretkey)
         return httpPost(self.__url,ORDER_INFO_RESOURCE,params)

    #现货批量订单信息查询
    def orders_info(self,symbol,order_ids, tradeType=0):
         ORDERS_INFO_RESOURCE = "/api/v1/orders_info.do"
         params = {
             'api_key':self.__apikey,
             'symbol':symbol,
             'order_id':','.join(order_ids),
             'type':tradeType
         }
         params['sign'] = buildMySign(params,self.__secretkey)
         return httpPost(self.__url,ORDERS_INFO_RESOURCE,params)

    #现货获得历史订单信息
    def get_orders_history(self,symbol,status=0,currentPage=1,pageLength=200):
           ORDER_HISTORY_RESOURCE = "/api/v1/order_history.do"
           params = {
              'api_key':self.__apikey,
              'symbol':symbol,
              'status':status,
              'current_page':currentPage,
              'page_length':pageLength
           }
           params['sign'] = buildMySign(params,self.__secretkey)
           return httpPost(self.__url,ORDER_HISTORY_RESOURCE,params)















    
