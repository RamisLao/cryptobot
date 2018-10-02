#!/usr/bin/env python
# -*- coding: utf-8 -*-
#Max number of requests: 300 / 5min

import hashlib
import hmac
import json
import time
import requests
from urlparse import urlparse
from urllib import urlencode
from bitsoErrors import ApiError, ApiClientError
from bitsoModels import Ticker, OrderBook, Balances, Fees, Trade, UserTrade, Order, TransactionQuote, TransactionOrder, LedgerEntry, Withdrawal, Funding, AvailableBooks, AccountStatus
import os

import pprint

import sys
sys.path.append("../")


def current_milli_time():
    nonce =  str(int(round(time.time() * 1000000)))
    return nonce
    
class TradeClient(object):
    """To use the private endpoints, initiate bitsoAPI.TradeClient with a client_id,
      api_key, and api_secret (see https://bitso.com/developers?shell#private-endpoints):
      
        >>> api = bitso.Api(API_KEY, API_SECRET)
        >>> balance = api.balance()
        >>> print balance.btc_available
        >>> print balance.mxn_available
    """
    
    def __init__(self, key=None, secret=None):
        """Instantiate a bitsoAPI.TradeClient object.
        
        Args:
          key:
            Bitso API Key 
          secret:
            Bitso API Secret

  
        """
        self.base_url_v2 = "https://bitso.com/api/v2"
        self.base_url = "https://bitso.com/api/v3"
        self.key = key
        self._secret = secret
        self.helper_functions = HelperFunctions(self.key, self._secret)
        
        
    def place_order(self, **kwargs):
        """Places a buy limit order.

        Args:
          book (str):
            Specifies which book to use. 
          side (str):
            the order side (buy or sell) 
          order_type (str):
            Order type (limit or market)
          major (str):
            The amount of major currency for this order. An order could be specified in terms of major or minor, never both.
          minor (str):
            The amount of minor currency for this order. An order could be specified in terms of major or minor, never both.
          price (str):
            Price per unit of major. For use only with limit orders.


        Returns:
          A bitso.Order instance.        
        """

        if kwargs.get('book') is None:
            raise ApiClientError({u'message': u'book not specified.'})
        if kwargs.get('side') is None:
            raise ApiClientError({u'message': u'side not specified.'})
        if kwargs.get('type') is None:
            raise ApiClientError({u'message': u'order type not specified.'})

        url = '%s/orders/' % self.base_url
        parameters = {}
        parameters['book'] = kwargs.get('book')
        parameters['type'] = kwargs.get('type')
        parameters['side'] = kwargs.get('side')
        if 'major' in kwargs:
            parameters['major'] = str(kwargs['major']).encode('utf-8')
        if 'minor' in kwargs:
            parameters['minor'] = str(kwargs['minor']).encode('utf-8')
        if 'price' in kwargs:
            parameters['price'] = str(kwargs['price']).encode('utf-8')

        resp = self.helper_functions.request_url(url, 'POST', params=parameters, private=True)
        return resp['payload']
    
    
    def cancel_order(self, oids):
        """Cancels an open order

        Args:
          order_id (str):
            A Bitso Order ID.
            
        Returns:
          A list of Order IDs (OIDs) for the canceled orders. Orders may not be successfully cancelled if they have been filled, have been already cancelled, or the OIDs are incorrect.        
        """
        if isinstance(oids, basestring):
            oids = [oids]        
        url = '%s/orders/' % self.base_url
        url+='%s/' % ('-'.join(oids))
        resp = self.helper_functions.request_url(url, 'DELETE', private=True)
        return resp['payload']
    
    
    def withdrawal(self, payload):
        """Triggers a "currency" withdrawal from your account
        
        =args=
            - withdraw_type (str): The currency to withdraw
            - amount (str): The amount of currency to withdraw from your account
            - address (str): The cryptocurrency address to send the amount to
        """
        url = '%s/%s_withdrawal/' % (self.base_url, payload["withdraw_type"])
        parameters = {}
        
        if payload["withdraw_type"] == "ripple":
            parameters['currency'] = str(payload["withdraw_type"]).encode('utf-8')
        parameters["amount"] = str(payload["amount"]).encode('utf-8')
        parameters["address"] = payload["address"]
        resp = self.helper_functions.request_url(url, 'POST', params=parameters, private=True)
        
        withdrawal_obj = Withdrawal._NewFromJsonDict(resp['payload'])
        obj_to_dict = self.helper_functions._convert_object_to_dict(withdrawal_obj)
        
        return obj_to_dict
        
    
    def account_status(self):
        """
        Get a user's account status.

        Returns:
          A bitso.AccountStatus instance.        
        """
        url = '%s/account_status/' % self.base_url
        resp = self.helper_functions.request_url(url, 'GET', private=True)
        return AccountStatus._NewFromJsonDict(resp['payload'])
    
    
    def balances(self):
        """Get a user's balance.

        Returns:
          A list of bitso.Balance instances.        
        """

        url = '%s/balance/' % self.base_url
        resp = self.helper_functions.request_url(url, 'GET', private=True)
        
        balances_obj = Balances._NewFromJsonDict(resp['payload'])
        obj_to_dict = self.helper_functions._convert_object_to_dict(balances_obj)
        
        payload = {}
        
        for currency, balance_obj in obj_to_dict.items():
            payload[currency] = self.helper_functions._convert_object_to_dict(balance_obj)
        
        return payload

  
    def fees(self):
        """Get a user's fees for all available order books.

        Returns:
          A list bitso.Fees instances.        
        """

        url = '%s/fees/' % self.base_url
        resp = self.helper_functions.request_url(url, 'GET', private=True)
        return Fees._NewFromJsonDict(resp['payload'])



    def ledger(self, operations='', marker=None, limit=25, sort='desc'):
        """Get the ledger of user operations 

        Args:
          operations (str, optional):
            They type of operations to include. Enum of ('trades', 'fees', 'fundings', 'withdrawals')
            If None, returns all the operations.
          marker (str, optional):
            Returns objects that are older or newer (depending on 'sort') than the object which
            has the marker value as ID
          limit (int, optional):
            Limit the number of results to parameter value, max=100, default=25
          sort (str, optional):
            Sorting by datetime: 'asc', 'desc'
            Defuault is 'desc'

        Returns:
          A list bitso.LedgerEntry instances.
        """
        url = '%s/ledger/%s' % (self.base_url, operations)
        parameters = {}
        if marker:
            parameters['marker'] = marker
        if limit:
            parameters['limit'] = limit
        if sort:
            parameters['sort'] = sort

        #headers = self._build_auth_header('GET', self._build_url(url, parameters))
        resp = self.helper_functions.request_url(url, 'GET', params=parameters, private=True)
        ledger_list = [LedgerEntry._NewFromJsonDict(entry) for entry in resp['payload']]
        for ledger in ledger_list:
            print(self.helper_functions._convert_object_to_dict(ledger))
        ledger_obj = ledger_list[0]
        
        obj_to_dict = self.helper_functions._convert_object_to_dict(ledger_obj)
        
        return obj_to_dict


    def withdrawal_status(self, wids=[], marker=None, limit=1, sort='desc'):
        """Get the ledger of user operations 

        Args:
          wids (list, optional):
            Specifies which withdrawal objects to return
          marker (str, optional):
            Returns objects that are older or newer (depending on 'sort') than the object which
            has the marker value as ID
          limit (int, optional):
            Limit the number of results to parameter value, max=100, default=25
          sort (str, optional):
            Sorting by datetime: 'asc', 'desc'
            Defuault is 'desc'

        Returns:
          A list bitso.Withdrawal instances.
        """
        if isinstance(wids, basestring):
            wids = [wids]
        
        url = '%s/withdrawals/' % (self.base_url)
        if wids:
            url+='%s/' % ('-'.join(wids))
        parameters = {}
        if marker:
            parameters['marker'] = marker
        if limit:
            parameters['limit'] = limit
        if sort:
            parameters['sort'] = sort
        resp = self.helper_functions.request_url(url, 'GET', params=parameters, private=True)
        withdrawal_list = [Withdrawal._NewFromJsonDict(entry) for entry in resp['payload']]
        
        if limit == 1:
            withdrawal_obj = withdrawal_list[0]
            
            obj_to_dict = self.helper_functions._convert_object_to_dict(withdrawal_obj)
        else:
            obj_to_dict = [self.helper_functions._convert_object_to_dict(withdrawal) \
                           for withdrawal in withdrawal_list]
        
        return obj_to_dict
    
        
    def user_trades(self, tids=[], book=None, marker=None, limit=25, sort='desc'):
        """Get a list of the user's transactions

        Args:
           book (str):
            Specifies which order book to get user trades from. 
          marker (str, optional):
            Returns objects that are older or newer (depending on 'sort') than the object which
            has the marker value as ID
          limit (int, optional):
            Limit the number of results to parameter value, max=100, default=25
          sort (str, optional):
            Sorting by datetime: 'asc', 'desc'
            Defuault is 'desc'
         
        Returns:
          A list bitso.UserTrade instances.        
        """

        url = '%s/user_trades/' % self.base_url
        if isinstance(tids, int):
            tids = str(tids)
        if isinstance(tids, basestring):
            tids = [tids]
        tids = map(str, tids)
        if tids:
            url+='%s/' % ('-'.join(tids))            
        if book:
            url+='?book=%s' % book
        parameters = {}
        if marker:
            parameters['marker'] = marker
        if limit:
            parameters['limit'] = limit
        if sort:
            if not isinstance(sort, basestring) or sort.lower() not in ['asc', 'desc']:
                 raise ApiClientError({u'message': u"sort is not 'asc' or 'desc' "})
            parameters['sort'] = sort
        resp = self.helper_functions.request_url(url, 'GET', params=parameters, private=True)
        order_list = [UserTrade._NewFromJsonDict(x) for x in resp['payload']]
        order_obj = order_list[0]
        
        obj_to_dict = self.helper_functions._convert_object_to_dict(order_obj)
        return obj_to_dict
    

    def open_orders(self, book=None):
        """Get a list of the user's open orders

        Args:
          book (str):
            Specifies which book to use. Default is btc_mxn
            
        Returns:
          A list of bitso.Order instances.        
        """
        url = '%s/open_orders/' % self.base_url
        url+='?book=%s' % book
        parameters = {}
        resp = self.helper_functions.request_url(url, 'GET', params=parameters, private=True)
        return [Order._NewFromJsonDict(x) for x in resp['payload']]


    def status_order(self, oids):
        """Get a list of details for one or more orders

        Args:
          order_ids (list):
            A list of Bitso Order IDs
            
        Returns:
          A list of bitso.Order instances.        
        """
        if isinstance(oids, basestring):
            oids = [oids]
        url = '%s/orders/' % self.base_url
        if oids:
            url+='%s/' % ('-'.join(oids))
        resp = self.helper_functions.request_url(url, 'GET', private=True)
        order_list = [Order._NewFromJsonDict(x) for x in resp['payload']]
        order_obj = order_list[0]
        
        obj_to_dict = self.helper_functions._convert_object_to_dict(order_obj)
        return obj_to_dict
    
    
    def get_address(self, currency):
        """
        Get current Bitso address to deposit bitcoins from an external exchange
        
        =args=
            - currency: name of cryptocurrency, e.g. btc.
        """
        url = "%s/funding_destination/" % self.base_url
        
        parameters = {"fund_currency" : currency}
        
        resp = self.helper_functions.request_url(url, "GET", params=parameters, private=True)
        
        return resp
    

class Client(object):
    """A python interface for the Bitso API

    Example usage:
      To create an instance of the bitsoAPI.Client class, without authentication:
      
        >>> import bitso
        >>> api = bitso.Api()
      
      To get the Bitso price ticker:
      
        >>> ticker = api.ticker()
        >>> print ticker.ask
        >>> print ticker.bid
    """
    
    def __init__(self):
        """Instantiate a bitsoAPI.Client object.
        
        Args:
          key:
            Bitso API Key 
          secret:
            Bitso API Secret

  
        """
        self.base_url_v2 = "https://bitso.com/api/v2"
        self.base_url = "https://bitso.com/api/v3"
        self.helper_functions = HelperFunctions()
        
    def available_books(self):
        """
        Returns:
          A list of bitso.AvilableBook instances
        """
        url = '%s/available_books/' % self.base_url
        resp = self.helper_functions.request_url(url, 'GET')
        return AvailableBooks._NewFromJsonDict(resp)

        
    def ticker(self, book):
        """Get a Bitso price ticker.

        Args:
          book (str):
            Specifies which book to use. 
            
        Returns:
          A bitso.Ticker instance.
        
        """
        url = '%s/ticker/' % self.base_url
        parameters = {}
        parameters['book'] = book
        resp = self.helper_functions.request_url(url, 'GET', params=parameters)
        
        ticker_obj = Ticker._NewFromJsonDict(resp['payload'])
        obj_to_dict = self.helper_functions._convert_object_to_dict(ticker_obj)
        return obj_to_dict


    def order_book(self, book, aggregate=True):
        """Get a public Bitso order book with a 
        list of all open orders in the specified book
        

        Args:
          book (str):
            Specifies which book to use. Default is btc_mxn
          aggregate (bool):
            Specifies if orders should be aggregated by price
            
        Returns:
          A bitso.OrderBook instance.
        
        """

        url = '%s/order_book/' % self.base_url
        parameters = {}
        parameters['book'] = book
        parameters['aggregate'] = aggregate
        resp = self.helper_functions.request_url(url, 'GET', params=parameters)
        orders_obj = OrderBook._NewFromJsonDict(resp['payload'])
        
        obj_to_dict = self.helper_functions._convert_object_to_dict(orders_obj)
        
        payload = {}
        
        payload["asks"] = []
        for order in obj_to_dict["asks"]:
            payload["asks"].append(self.helper_functions._convert_object_to_dict(order))
            
        payload["bids"] = []
        for order in obj_to_dict["bids"]:
            payload["bids"].append(self.helper_functions._convert_object_to_dict(order))
        
        return payload

    def trades(self, book, **kwargs):
        """Get a list of recent trades from the specified book.

        Args:
          book (str):
            Specifies which book to use. Default is btc_mxn

          marker (str, optional):
            Returns objects that are older or newer (depending on 'sort') than the object which
            has the marker value as ID
          limit (int, optional):
            Limit the number of results to parameter value, max=100, default=25
          sort (str, optional):
            Sorting by datetime: 'asc', 'desc'
            Defuault is 'desc'

            
        Returns:
          A list of bitso.Trades instances.        
        """

        url = '%s/trades/' % self.base_url
        parameters = {}
        parameters['book'] = book        
        if 'marker' in kwargs:
            parameters['marker'] = kwargs['marker']
        if 'limit' in kwargs:
            parameters['limit'] = kwargs['limit']
        if 'sort' in kwargs:
            parameters['sort'] = kwargs['sort']
        resp = self.helper_functions.request_url(url, 'GET', params=parameters)
        return [Trade._NewFromJsonDict(x) for x in resp['payload']]
        

class HelperFunctions(object):
    """Helper functions for the Bitso API"""
    
    def __init__(self, key=None, secret=None):
        """Instantiate a bitsoAPI.HelperFunctions object.
        
        Args:
          key:
            Bitso API Key 
          secret:
            Bitso API Secret

  
        """
        self.base_url_v2 = "https://bitso.com/api/v2"
        self.base_url = "https://bitso.com/api/v3"
        self.key = key
        self._secret = secret

    
    def _build_auth_payload(self):
        parameters = {}
        parameters['key'] = self.key
        parameters['nonce'] = str(int(time.time()))
        msg_concat = parameters['nonce']+self.client_id+self.key
        parameters['signature'] = hmac.new(self._secret.encode('utf-8'),
                                           msg_concat.encode('utf-8'),
                                           hashlib.sha256).hexdigest()
        return parameters

    def _build_auth_header(self, http_method, url, json_payload=''):
        if json_payload == {} or json_payload=='{}':
            json_payload = ''
        url_components = urlparse(url)
        request_path = url_components.path
        if url_components.query != '':
            request_path+='?'+url_components.query
        nonce = current_milli_time()
        msg_concat = nonce+http_method.upper()+request_path+json_payload
        signature = hmac.new(self._secret.encode('utf-8'),
                                 msg_concat.encode('utf-8'),
                                 hashlib.sha256).hexdigest()
        return {'Authorization': 'Bitso %s:%s:%s' % (self.key, nonce, signature)}

    
    def request_url(self, url, verb, params=None, private=False):
        headers=None
        if params == None:
            params = {}
        if private:
            headers = self._build_auth_header(verb, url, json.dumps(params))
        if verb == 'GET':
            url = self._build_url(url, params)
            if private:
                headers = self._build_auth_header(verb, url)
            error = True
            while error:
                error = False
                try:
                    resp = requests.get(url, headers=headers)
                except requests.exceptions.Timeout:
                    print("Request Timeout!")
                    time.sleep(60)
                    error = True
                except requests.RequestException as e:
                    print("Fatal Error!")
                    print(str(e))
        elif verb == 'POST':
            error = True
            while error:
                error = False
                try:
                    resp = requests.post(url, json=params, headers=headers)
                except requests.exceptions.Timeout:
                    print("Request Timeout!")
                    time.sleep(60)
                    error = True
                except requests.RequestException as e:
                    print("Fatal Error!")
                    print(str(e))
        elif verb == 'DELETE':
            error = True
            while error:
                error = False
                try:
                    resp = requests.delete(url, headers=headers)
                except requests.exceptions.Timeout:
                    print("Request Timeout!")
                    time.sleep(60)
                    error = True
                except requests.RequestException as e:
                    print("Fatal Error!")
                    print(str(e))
                
        try:
            data = self._parse_json(resp.content.decode('utf-8'))
        except Exception:
            time.sleep(300)
            data = self.request_url(url, verb, params=params, private=private)
        return data

    def _build_url(self, url, params):
        if params and len(params) > 0:
            url = url+'?'+self._encode_parameters(params)
        return url

    def _encode_parameters(self, parameters):
        if parameters is None:
            return None
        else:
            param_tuples = []
            for k,v in parameters.items():
                if v is None:
                    continue
                if isinstance(v, (list, tuple)):
                    for single_v in v:
                        param_tuples.append((k, single_v))
                else:
                    param_tuples.append((k,v))
            return urlencode(param_tuples)


         
    def _parse_json(self, json_data):
        try:
            data = json.loads(json_data)
            self._check_for_api_error(data)
        except:
            print("Error!")
            print(json_data)
            raise
        return data

    def _check_for_api_error(self, data):
        if data['success'] != True:
            raise ApiError(data['error'])
        if 'error' in data:
            raise ApiError(data['error'])
        if isinstance(data, (list, tuple)) and len(data)>0:
            if 'error' in data[0]:
                raise ApiError(data[0]['error'])
                
    def _convert_object_to_dict(self, obj):
        """Convert a bitsoModels.py object to a dictionary
        
        =args=
            - obj: bitsoModels.py object
        """
        
        attr_list = [a for a in dir(obj) if not a.startswith('_') and not callable(getattr(obj, a))]

        obj_dict = {}

        for attr in attr_list:
            if attr == "last":
                obj_dict["last_price"] = float(getattr(obj, attr))
            else:
                try:
                    obj_dict[attr] = float(getattr(obj, attr))
                except:
                    obj_dict[attr] = getattr(obj, attr)

        return obj_dict

"""
with open(os.path.expanduser('~') + '/.keys.json', 'r') as f:
        to_string = f.read()
        keys = json.loads(to_string)
        
client = TradeClient(keys["bitso"]["key"], keys["bitso"]["secret"])



print(pprint.pprint(client.balances()))

transaction = {"book": "btc_mxn",
               "type" : "market",
               "side" : "sell",
               "major" : 0.5}

#print(pprint.pprint(client.open_orders("btc_mxn")))
#client.ledger(operations="withdrawals", limit=5)
#client.cancel_order("q3cjvOJdvkdqng12")
print(pprint.pprint(client.status_order("OmH4RXs7wo8ga5oY")))
#print(client.get_address("btc"))

#non_client = Client()
"""

    
