#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 31 10:29:14 2018

@author: joseramon
"""

from bitso import bitsoAPI
from bitfinex import bitfinexAPI

class Config:
    
    def __init__(self, keys=None, thresh=None, mid_thresh=None, interval=None, percentage=None, extra=None):
        
        self._cryptocurrencies = "bitcoin"
        self._exchanges = ["bitfinex", "bitso"]
        self._apis_dict = {"bitfinex" : bitfinexAPI,
                     "bitso" : bitsoAPI}
        self._books_dict = {"bitcoin" : {"bitfinex" : "btcusd",
                                   "bitso": "btc_mxn"}}
        self._currency_for_address = {"bitcoin" : {"bitfinex" : "bitcoin",
                                                   "bitso": "btc"}}
        self._ids = {"bitfinex" : "order_id",
                     "bitso" : "oid"}
    
        self._keys = keys
        
        #Thresholds for Engine
        self.thresh = thresh
        self.mid_thresh = mid_thresh
        
        #Repetition rate for Bot
        self.interval = interval
        
        #Percentage
        self._percentage = percentage
        
        #Extra
        self._extra = extra
        
    def get_exchanges(self):
        return self._exchanges
    
    def get_apis(self):
        return self._apis_dict
    
    def get_books(self):
        return self._books_dict
    
    def get_currency_for_address(self):
        return self._currency_for_address
    
    def get_cryptocurrencies(self):
        return self._cryptocurrencies
    
    def get_keys(self):
        return self._keys
    
    def get_ids(self):
        return self._ids
    
    def get_percentage(self):
        return self._percentage
    
    def get_extra(self):
        return self._extra
    