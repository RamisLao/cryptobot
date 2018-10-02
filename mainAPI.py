#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 19 07:42:06 2018

@author: joseramon
"""

import datetime

LOGS = "./logs/mainApi_logs.txt"

class TradeClient:
    "Private Client to buy and sell cryptocurrencies in multiple exchanges"""
    
    def __init__(self, keys, config, transaction=None):
        """
        =args=
            - apis : dictionary mapping exchanges' names to their api modules
        """
        
        self._keys = keys
        self._config = config
        self._books = self._config.get_books()
        self._clients = {}
        
        self.set_clients(self._config.get_apis())
        
        self._transaction = transaction
                
    def set_clients(self, apis):
        """Create  dictionary that contains all the TradeClient() classes from the different
        exchanges that we are using.
        
        =args=
            - apis : dictionary mapping exchanges' names to their api modules
        """
        
        for exchange, api in apis.items():
            self._clients[exchange] = api.TradeClient(self._keys[exchange]['key'], \
                                                      self._keys[exchange]['secret'])
            
    def change_transaction(self, new_transaction):
        self._transaction = new_transaction
            
    def run(self):
        """Run transaction"""
        response = self.select_request()
        return response 
            
    
    def select_request(self):
        """Separate orders from transfers"""
        
        if self._transaction == None:
            response = self.balances()
        elif self._transaction["type"] == "order":
            response = self.execute_order()
        elif self._transaction["type"] == "withdrawal":
            response = self.execute_withdrawal()
        elif self._transaction["type"] == "addresses":
            response = self.get_addresses(self._transaction["currency"])
        
        return response
    
    def execute_order(self): #!!! What happens if buy is accepted but sell fails?
        """Execute buy and sell orders. Returns dictionary with schema:
            
            {exchange name : response,
             exchange name : response}
            
        """
        
        responses = {}
        
        order = self._transaction["payload"]
        
        buy = order["buy"]
        if buy != None:
            buy_exchange = buy["exchange"]
            response_buy = self.buy_and_sell(buy, "buy")
            responses[buy_exchange] = response_buy
        
        sell = order["sell"]
        if sell != None:
            sell_exchange = sell["exchange"]
            response_sell = self.buy_and_sell(sell, "sell")
            responses[sell_exchange] = response_sell
        
        return responses
    
    def buy_and_sell(self, order, side):
        """Takes an order dict and places an order in the TradeClient.
        
        =args=
            - order : dictionary containing the following data =>
                            {"exchange" : string,
                              "symbol" : string,
                              "amount" : float,
                              "price" : float,
                              "type" : string}
            - side : "buy" or "sell"
        """
        
        payload = {}
        
        payload["exchange"] = order["exchange"]
        payload["book"] = self._books[order["symbol"]][order["exchange"]]
        payload["side"] = side
        payload["major"] = order["amount"]
        if payload["exchange"] == "bitfinex":
            payload["price"] = order["price"]
        payload["type"] = order["type"]
        
        client = self._clients[order["exchange"]]
        
        try:
            response = client.place_order(**payload)
        except Exception as e:
            self.store_error(e)
            
            return
        
        self.store_to_log("None", "Buy/Sell order executed", response)
        
        return response
        
    def cancel_order(self, exchange, order_id):
        """Cancel order with id order_id
        
        =args=
            - exchange : exchange in which you want to cancel an order
            - order_id : an order id
        """
        
        client = self._clients[exchange]
        response = client.cancel_order(order_id)
        return response
    
    def execute_withdrawal(self):
        """
        Withdraw crytpocurrency from exchange "from" to the address of "to".
        
        =args=
            - from : exchange to withdraw from
            - to : exchange to withdraw to
            - withdraw_type : the currency you are trying to withdraw
            - amount : amount to withdraw
        """
        withdrawal = self._transaction["payload"]
        payload = {"withdraw_type" : withdrawal["withdraw_type"],
                   "amount" : withdrawal["amount"],
                   "address" : withdrawal["addresses"][withdrawal["to"]]}
        
        client = self._clients[withdrawal["from"]]
        
        try:
            response = client.withdrawal(payload)
        except Exception as e:
            self.store_error(e)
            
            return
        
        self.store_to_log("None", "Withdrawal executed", response)
            
        return response
        
    def balances(self):
        """Ask for client's balances. Return a dictionary with the form:
            
            {"type" : "balances",
            "payload" : {
                    "bitfinex" : {"btc" :
                                      {"name" : "btc",
                                      "total" : "1000",
                                      "locked" : "250",
                                      "available" : "750"},
                                  "usd" :
                                      {"name" : "usd",
                                      "total" : "2000",
                                      "locked" : "500",
                                      "available" : "1500"}
                                  },
                    "bitso" : {"btc" :
                                      {"name" : "btc",
                                      "total" : "1000",
                                      "locked" : "250",
                                      "available" : "750"},
                               "mxn" :
                                      {"name" : "mxn",
                                      "total" : "2000",
                                      "locked" : "500",
                                      "available" : "1500"}
                               }
                          }
            }
        """
        
        payload = {}
        
        for exchange, client in self._clients.items():
            payload[exchange] = client.balances()
            
        balances = {"type" : "balances",
                    "payload" : payload}
        
        return balances
    
    
    def get_addresses(self, currency):
        """Get deposit addresses for Bitso and Bitfinex.
        
        =args=
            - currency: Name of cryptocurrency that we want to withdraw and deposit.
        """
        payload = {}
        
        for exchange, client in self._clients.items():
            payload[exchange] = client.get_address(self._config.get_currency_for_address()[currency][exchange])
            
        addresses = {"type" : "addresses",
                     "payload" : payload}
        
        return addresses
    
    
    def check_status(self):
        if self._transaction["type"] == "order_status":
            response = self.order_status()
        if self._transaction["type"] == "withdrawal_status":
            response = self.withdrawal_status()
        
        return response
    
    def order_status(self):
        try:
            client = self._clients[self._transaction["exchange"]]
            response = client.status_order(self._transaction["id"])
            
        except Exception as e:
            self.store_error(e)
            
            return
        
        self.store_to_log("None", "Check Order Status", response)
        
        return response
    
    def withdrawal_status(self):
        client = self._clients[self._transaction["exchange"]]
        
        try:
            if self._transaction["exchange"] == "bitfinex":
                response = client.withdrawal_status("BTC")
            elif self._transaction["exchange"] == "bitso":
                response = client.withdrawal_status(self._transaction["id"])
        except Exception as e:
            self.store_error(e)
            
            return
        
        self.store_to_log("None", "Check Withdrawal Status", response)
            
        return response
    
    def store_to_log(self, balances, status, data):
        
        log = """----------------------------------------\n\n""" + datetime.datetime.now() + """\n\n
            Current balances: """ + str(balances) + """\n\n    
            Status: """ + str(status) + """\n\n
            Data: """ + str(data) + """\n\n"""
        
        with open(LOGS, 'a') as logs:
            logs.write(log)
            
    def store_error(self, error):
        self.store_to_log("None", "Error", error)
        

class Client:
    """Public Client that communicates with each exchange API to get the bids and asks"""
    
    def __init__(self, config):
        """
        =args=
            - apis : dictionary mapping exchanges' names to their api modules
        """
        
        self._config = config
        self._clients = {}
        
        self.set_clients(self._config.get_apis())
        
        self._books = self._config.get_books()
        
    def set_clients(self, apis):
        """Create a dictionary that contains all the Client() classes from the different
        exchanges that we are using.
        
        =args=
            - apis: dictionary mapping exchange names to their api modules
        """
        
        for exchange, api in apis.items():
            self._clients[exchange] = api.Client()
                
    def ticker(self, currency):
        """GET request that returns trading information for the specified coin.
        
        =args=
            - coin: coin name, e.g. bitcoin, litecoin, ethereum, etc.
        """
        tickers = {}
        
        books = self._books[currency]
        
        for exchange, client in self._clients.items():
            book_name = books[exchange]
            tickers[exchange] = client.ticker(book_name)
            
        return tickers   
    
    def order_books(self, currency):
        """GET request that returns the order book for both exchanges
        
        =args=
            - currency: currency name, e.g. bitcoin, litecoin, ethereum, etc.
        """
        order_books = {}
        
        books = self._books[currency]
        
        for exchange, client in self._clients.items():
            book_name = books[exchange]
            order_books[exchange] = client.order_book(book_name)
            
        return order_books




