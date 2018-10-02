# -*- coding: utf-8 -*-
#!/usr/bin/env python

from __future__ import absolute_import
import requests
import json
import base64
import hmac
import hashlib
import time
import os
import pprint
import datetime

PROTOCOL = "https"
HOST = "api.bitfinex.com"
VERSION = "v1"

PATH_SYMBOLS = "symbols"
PATH_TICKER = "pubticker/%s"
PATH_TODAY = "today/%s"
PATH_STATS = "stats/%s"
PATH_LENDBOOK = "lendbook/%s"
PATH_ORDERBOOK = "book/%s"

# HTTP request timeout in seconds
TIMEOUT = 5.0

class TradeClient:
    """
    Authenticated client for trading through Bitfinex API
    """

    def __init__(self, key, secret):
        self.URL = "{0:s}://{1:s}/{2:s}".format(PROTOCOL, HOST, VERSION)
        self.KEY = key
        self.SECRET = secret
        pass

    @property
    def _nonce(self):
        """
        Returns a nonce
        Used in authentication
        """
        #return str(time.time() * 1000000)
        nonce =  str(int(round(time.time() * 1000000)))
        return nonce

    def _sign_payload(self, payload):
        j = json.dumps(payload)
        data = base64.standard_b64encode(j.encode('utf8'))

        h = hmac.new(self.SECRET.encode('utf8'), data, hashlib.sha384)
        signature = h.hexdigest()
        return {
            "X-BFX-APIKEY": self.KEY,
            "X-BFX-SIGNATURE": signature,
            "X-BFX-PAYLOAD": data
        }

    def place_order(self, **kwargs):
        """
        Submit a new order.
        :param amount:
        :param price:
        :param side:
        :param ord_type:
        :param symbol:
        :param exchange:
        :return:
        """
        print(kwargs['book'])
        assert kwargs['book'] is not None, "Book not specified"
        assert kwargs['side'] is not None, "Side not specified"
        assert kwargs['type'] is not None, "Order type not specified"
        
        payload = {"request": "/v1/order/new",
                   "nonce": self._nonce}
        
        payload["exchange"] = kwargs.get('exchange')
        #payload["symbol"] = kwargs.get('book')
        payload["symbol"] = "BTCUSD"
        payload["type"] = kwargs.get('type')
        payload["side"] = kwargs.get('side')
        payload["amount"] = str(kwargs.get('major')).encode('utf-8')
        
        if 'price' in kwargs:
            payload["price"] = str(kwargs.get('price')).encode('utf-8')
            
        print(payload)

        signed_payload = self._sign_payload(payload)
        
        error = True
        while error:
            error = False
            try:
                r = requests.post(self.URL + "/order/new", headers=signed_payload, verify=True)
            except requests.exceptions.Timeout:
                print("Request Timeout!")
                error = True
                time.sleep(60)
            except requests.exceptions.RequestException as e:
                print("Fatal Error!")
                print(str(e))
                
        json_resp = r.json()

        try:
            json_resp['order_id']
        except:
            return json_resp['message']

        return json_resp

    def cancel_order(self, order_id):
        """
        Cancel an order.
        :param order_id:
        :return:
        """
        payload = {
            "request": "/v1/order/cancel",
            "nonce": self._nonce,
            "order_id": order_id
        }

        signed_payload = self._sign_payload(payload)
        r = requests.post(self.URL + "/order/cancel", headers=signed_payload, verify=True)
        json_resp = r.json()

        try:
            json_resp['avg_execution_price']
        except:
            return json_resp['message']

        return json_resp
    
    
    def withdrawal(self, payload):
        """
        Withdraw crytpocurrency to an address
        
        =args=
            - withdraw_type : define the currency you are trying to withdraw
            - amount : amount to withdraw
            - address : destination address for withdrawal
        """
        new_payload = {
                "request" : "/v1/withdraw",
                "withdraw_type" : payload["withdraw_type"],
                "walletselected" : "exchange",
                "amount" : payload["amount"],
                "address" : payload["address"],
                "nonce" : self._nonce,
        }
        
        signed_payload = self._sign_payload(new_payload)
        
        error = True
        while error:
            error = False
            try:
                r = requests.post(self.URL + "/withdraw", headers=signed_payload, verify=True)
            except requests.exceptions.Timeout:
                print("Request Timeout!")
                error = True
                time.sleep(60)
            except requests.exceptions.RequestException as e:
                print("Fatal Error!")
                print(str(e))
        
        json_resp = r.json()
        
        return json_resp
    

    def delete_all_orders(self):
        """
        Cancel all orders.
        :return:
        """
        payload = {
            "request": "/v1/order/cancel/all",
            "nonce": self._nonce,
        }

        signed_payload = self._sign_payload(payload)
        r = requests.post(self.URL + "/order/cancel/all", headers=signed_payload, verify=True)
        json_resp = r.json()
        return json_resp

    def status_order(self, order_id):
        """
        Get the status of an order. Is it active? Was it cancelled? To what extent has it been executed? etc.
        :param order_id:
        :return:
        """
        payload = {
            "request": "/v1/order/status",
            "nonce": self._nonce,
            "order_id": order_id
        }

        signed_payload = self._sign_payload(payload)
        
        error = True
        while error:
            error = False
            try:
                r = requests.post(self.URL + "/order/status", headers=signed_payload, verify=True)
            except requests.exceptions.Timeout:
                print("Request Timeout!")
                error = True
                time.sleep(60)
            except requests.exceptions.RequestException as e:
                print("Fatal Error!")
                print(str(e))
        
        json_resp = r.json()

        try:
            json_resp['avg_execution_price']
        except:
            return json_resp['message']

        return json_resp

    def active_orders(self):
        """
        Fetch active orders
        """

        payload = {
            "request": "/v1/orders",
            "nonce": self._nonce
        }

        signed_payload = self._sign_payload(payload)
        r = requests.post(self.URL + "/orders", headers=signed_payload, verify=True)
        json_resp = r.json()

        return json_resp
    

    def past_trades(self, timestamp=0, symbol='btcusd'):
        """
        Fetch past trades
        :param timestamp:
        :param symbol:
        :return:
        """
        payload = {
            "request": "/v1/mytrades",
            "nonce": self._nonce,
            "symbol": symbol,
            "timestamp": timestamp
        }

        signed_payload = self._sign_payload(payload)
        r = requests.post(self.URL + "/mytrades", headers=signed_payload, verify=True)
        json_resp = r.json()

        return json_resp

    def balances(self):
        """
        Fetch balances
        :return:
        """
        payload = {
            "request": "/v1/balances",
            "nonce": self._nonce
        }

        signed_payload = self._sign_payload(payload)
        
        error = True
        while error:
            error = False
            try:
                r = requests.post(self.URL + "/balances", headers=signed_payload, verify=True)
            except requests.exceptions.Timeout:
                print("Request Timeout!")
                error = True
                time.sleep(60)
            except requests.exceptions.RequestException as e:
                print("Fatal Error!")
                print(str(e))
        
        json_resp = r.json()
                
        payload = {}
        
        try:
            error_message = json_resp["message"]
            print("ERROR: " + error_message)
            return
        except:
        
            for item in json_resp:
                if item["type"] == "exchange":
                    if item["currency"] == "btc" or item["currency"] == "usd":
                        payload[item["currency"]] = {"name" : item["currency"],
                             "total" : item["amount"],
                             "locked" : str(float(item["amount"]) - float(item["available"])),
                             "available" : item["available"]}

        return payload

    def history(self, currency, since=0, until=9999999999, limit=5, wallet='exchange'):
        """
        View you balance ledger entries
        :param currency: currency to look for
        :param since: Optional. Return only the history after this timestamp.
        :param until: Optional. Return only the history before this timestamp.
        :param limit: Optional. Limit the number of entries to return. Default is 500.
        :param wallet: Optional. Return only entries that took place in this wallet. Accepted inputs are: “trading”,
        "exchange", "deposit".
        """
        payload = {
            "request": "/v1/history",
            "nonce": self._nonce,
            "currency": currency,
            "since": since,
            "until": until,
            "limit": limit,
            "wallet": wallet
        }
        signed_payload = self._sign_payload(payload)
        r = requests.post(self.URL + "/history", headers=signed_payload, verify=True)
        json_resp = r.json()

        return json_resp

    def withdrawal_status(self, currency, limit=1):
        """
        View you balance ledger entries
        :param currency: currency to look for
        :param since: Optional. Return only the history after this timestamp.
        :param until: Optional. Return only the history before this timestamp.
        :param limit: Optional. Limit the number of entries to return. Default is 500.
        :param wallet: Optional. Return only entries that took place in this wallet. Accepted inputs are: “trading”,
        "exchange", "deposit".
        """
        payload = {
            "request": "/v1/history/movements",
            "nonce": self._nonce,
            "currency": currency,
            "limit": limit
        }
        signed_payload = self._sign_payload(payload)
        
        error = True
        while error:
            error = False
            try:
                r = requests.post(self.URL + "/history/movements", headers=signed_payload, verify=True)
            except requests.exceptions.Timeout:
                print("Request Timeout!")
                error = True
                time.sleep(60)
            except requests.exceptions.RequestException as e:
                print("Fatal Error!")
                print(str(e))
        
        json_resp = r.json()

        return json_resp
    
    def get_address(self, currency):
        """
        Get current Bitfinex address to deposit bitcoins from an external exchange
        
        =args=
            - currency: name of cryptocurrency, e.g. bitcoin.
        """
        payload = {
            "request" : "/v1/deposit/new",
            "nonce" : self._nonce,
            "method" : currency,
            "wallet_name" : "exchange"
        }
        signed_payload = self._sign_payload(payload)
        
        error = True
        while error:
            error = False
            try:
                r = requests.post(self.URL + "/deposit/new", headers=signed_payload, verify=True)
            except requests.exceptions.Timeout:
                print("Request Timeout!")
                error = True
                time.sleep(60)
            except requests.exceptions.RequestException as e:
                print("Fatal Error!")
                print(str(e))
        
        json_resp = r.json()
        
        return json_resp


class Client:
    """
    Client for the bitfinex.com API.
    See https://www.bitfinex.com/pages/api for API documentation.
    """

    def server(self):
        return u"{0:s}://{1:s}/{2:s}".format(PROTOCOL, HOST, VERSION)


    def url_for(self, path, path_arg=None, parameters=None):

        # build the basic url
        url = "%s/%s" % (self.server(), path)

        # If there is a path_arh, interpolate it into the URL.
        # In this case the path that was provided will need to have string
        # interpolation characters in it, such as PATH_TICKER
        if path_arg:
            url = url % (path_arg)

        # Append any parameters to the URL.
        if parameters:
            url = "%s?%s" % (url, self._build_parameters(parameters))

        return url


    def symbols(self):
        """
        GET /symbols
        curl https://api.bitfinex.com/v1/symbols
        ['btcusd','ltcusd','ltcbtc']
        """
        return self._get(self.url_for(PATH_SYMBOLS))


    def ticker(self, symbol):
        """
        GET /ticker/:symbol
        curl https://api.bitfinex.com/v1/ticker/btcusd
        {
            'ask': '562.9999',
            'timestamp': '1395552290.70933607',
            'bid': '562.25',
            'last_price': u'562.25',
            'mid': u'562.62495'}
        """
        data = self._get(self.url_for(PATH_TICKER, (symbol)))

        # convert all values to floats
        return self._convert_to_floats(data)


    def today(self, symbol):
        """
        GET /today/:symbol
        curl "https://api.bitfinex.com/v1/today/btcusd"
        {"low":"550.09","high":"572.2398","volume":"7305.33119836"}
        """

        data = self._get(self.url_for(PATH_TODAY, (symbol)))

        # convert all values to floats
        return self._convert_to_floats(data)


    def stats(self, symbol):
        """
        curl https://api.bitfinex.com/v1/stats/btcusd
        [
            {"period":1,"volume":"7410.27250155"},
            {"period":7,"volume":"52251.37118006"},
            {"period":30,"volume":"464505.07753251"}
        ]
        """
        data = self._get(self.url_for(PATH_STATS, (symbol)))

        for period in data:

            for key, value in period.items():
                if key == 'period':
                    new_value = int(value)
                elif key == 'volume':
                    new_value = float(value)

                period[key] = new_value

        return data

    def order_book(self, symbol, parameters=None):
        """
        curl "https://api.bitfinex.com/v1/book/btcusd"
        {"bids":[{"price":"561.1101","amount":"0.985","timestamp":"1395557729.0"}],"asks":[{"price":"562.9999","amount":"0.985","timestamp":"1395557711.0"}]}
        The 'bids' and 'asks' arrays will have multiple bid and ask dicts.
        Optional parameters
        limit_bids (int): Optional. Limit the number of bids returned. May be 0 in which case the array of bids is empty. Default is 50.
        limit_asks (int): Optional. Limit the number of asks returned. May be 0 in which case the array of asks is empty. Default is 50.
        eg.
        curl "https://api.bitfinex.com/v1/book/btcusd?limit_bids=1&limit_asks=0"
        {"bids":[{"price":"561.1101","amount":"0.985","timestamp":"1395557729.0"}],"asks":[]}
        """
        data = self._get(self.url_for(PATH_ORDERBOOK, path_arg=symbol, parameters=parameters))

        for type_ in data.keys():
            for list_ in data[type_]:
                for key, value in list_.items():
                    list_[key] = float(value)

        return data


    def _convert_to_floats(self, data):
        """
        Convert all values in a dict to floats
        """
        for key, value in data.items():
            data[key] = float(value)

        return data


    def _get(self, url):
        
        error = True
        while error:
            error = False
            try:
                r = requests.get(url, timeout=TIMEOUT).json()
            except requests.exceptions.Timeout:
                print("Request Timeout!")
                error = True
                time.sleep(60)
            except requests.exceptions.RequestException as e:
                print("Fatal Error!")
                print(str(e))
        
        return r


    def _build_parameters(self, parameters):
        # sort the keys so we can test easily in Python 3.3 (dicts are not
        # ordered)
        keys = list(parameters.keys())
        keys.sort()

        return '&'.join(["%s=%s" % (k, parameters[k]) for k in keys])

"""
with open(os.path.expanduser('~') + '/.keys.json', 'r') as f:
        to_string = f.read()
        keys = json.loads(to_string)
        
client = TradeClient(keys["bitfinex"]["key"], keys["bitfinex"]["secret"])
#print(pprint.pprint(client.get_address("bitcoin")))
#print(pprint.pprint(client.balances()))
#print(pprint.pprint(client.status_order(12026007558)["remaining_amount"]))
print(pprint.pprint(client.history("BTC")))
print(pprint.pprint(client.withdrawal_status("BTC", limit=1)))

non_client = Client()
#print(pprint.pprint(non_client.order_book("btcusd")))
"""