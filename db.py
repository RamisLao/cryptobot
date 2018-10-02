#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Apr  4 07:52:21 2018

@author: joseramon
"""
from datetime import datetime
from pymongo import MongoClient

class DB:
    
    """Class to handle communications with the MongoDB instance. The database's name is
    "cryptobot". The schema is as following:
        
        - collection => buysell_log:
            
            {
               "_id" : ObjectId(),
               "timestamp" : year-month-day hour:minute:second (e.g. 2018-04-07 20:35:35.884530),
                "type" : "order",
               "payload" : {
                    "buy" : {"exchange" : string (e.g. "bitfinex"),
                              "symbol" : string (e.g. "bitcoin"),
                              "amount" : float (e.g. 2045.6),
                              "price" : float (e.g. 4356.9),
                              "type" : string (e.g. "exchange limit")},
                    "sell" : {"exchange" : string,
                              "symbol" : string,
                              "amount" : float,
                              "price" : float,
                              "type" : string}
                    }_
            }
            
        - collection => withdrawal_log:
            
            {
                "_id" : ObjectId(),
                "timestamp" : year-month-day hour:minute:second (e.g. 2018-04-07 20:35:35.884530),
                  "type" : "withdrawal",
                  "payload" : {
                          "from" : string (e.g. "bitfinex"),
                          "to" : string (e.g. "bitso"),
                          "withdraw_type" : string (e.g. "bitcoin"),
                          "amount" : float (e.g. 3452.3),
                          }
            }
            
        - collection => balances_log:
        - collection => bot_status:
            
            {
                "_id" : ObjectId(),
                "timestamp" : year-month-day hour:minute:second (e.g. 2018-04-07 20:35:35.884530),
                "status" : int (e.g. 4),
                "transaction" : dict (contains "order" and "withdrawal"),
                "buysell_response" : dict (contains response from the exchange),
                "withdrawal_response" : dict (contains response from the exchange)
            }
            
        - collection => engine_status:
            
            {
                "_id" : ObjectId(),
                "timestamp" year-month-day hour:minute:second (e.g. 2018-04-07 20:35:35.884530): ,
                "status" : int (e.g. 4),
                "sell_buy" : ,
                "balance_order" : 
            }
    """
    
    def __init__(self):
        
        self._client = MongoClient('localhost', 27017)
        self._db = self._client['cryptobot']

    def store_to_buysell_log(self, doc):
        buysell_log = self._db['buysell_log']
        log_id = buysell_log.insert_one(doc).inserted_id
        
        return log_id
    
    def retrieve_from_buysell_log(self, doc_id):
        buysell_log = self._db['buysell_log']
        log = buysell_log.find_one({'_id' : doc_id})
        
        return log
    
    def store_to_withdrawal_log(self, doc):
        withdrawal_log = self._db['withdrawal_log']
        log_id = withdrawal_log.insert_one(doc).inserted_id
        
        return log_id
    
    def retrieve_from_withdrawal_log(self, doc_id):
        withdrawal_log = self._db['withdrawal_log']
        log = withdrawal_log.find_one({'_id' : doc_id})
        
        return log
    
    def store_to_balances(self, doc):
        balances_log = self._db['balances_log']
        log_id = balances_log.insert_one(doc).inserted_id
        
        return log_id
    
    def retrieve_from_balances(self, doc_id):
        balances_log = self._db['balances_log']
        log = balances_log.find_one({'_id' : doc_id})
        
        return log
    
    def store_to_bot_status(self, status, transaction, buy_sell, withdrawal):
        bot_status_coll = self._db["bot_status"]
        bot_status_coll.delete_one({})
        
        doc = {"datetime" : datetime.now(),
               "status" : status,
               "transaction" : transaction,
               "buy_sell" : buy_sell,
               "withdrawal" : withdrawal}
        
        coll_id = bot_status_coll.insert_one(doc).inserted_id
        
        return coll_id
    
    def retrieve_from_bot_status(self):
        bot_status_coll = self._db["bot_status"]
        log = bot_status_coll.find_one()
        
        return log
    
    def store_to_engine_status(self, status, sell_buy, balance_order, finish_cycle):
        engine_status_coll = self._db["engine_status"]
        engine_status_coll.delete_one({})
        
        doc = {"datetime" : datetime.now(),
               "status" : status,
               "sell_buy" : sell_buy,
               "balance_order" : balance_order,
               "finish_cycle" : finish_cycle}
        
        coll_id = engine_status_coll.insert_one(doc).inserted_id
        
        return coll_id
    
    def retrieve_from_engine_status(self):
        engine_status_coll = self._db["engine_status"]
        log = engine_status_coll.find_one()
        
        return log
    
    def store_last_total_usd(self, total_usd):
        total_usd_coll = self._db["total_usd"]
        total_usd_coll.delete_one({})
        
        doc = {"datetime" : datetime.now(),
                "total_usd" : total_usd}
        
        coll_id = total_usd_coll.insert_one(doc).inserted_id
        
        return coll_id
    
    def retrieve_last_total_usd(self):
        total_usd_coll = self._db["total_usd"]
        log = total_usd_coll.find_one()
        
        return log
    
    def store_to_mxnusd_price(self, time, price):
        engine_status_coll = self._db["mxnusd_price"]
        engine_status_coll.delete_one({})
        
        doc = {"time" : time,
               "price" : price}
        
        coll_id = engine_status_coll.insert_one(doc).inserted_id
        
        return coll_id
    
    def retrieve_from_mxnusd_price(self):
        engine_status_coll = self._db["mxnusd_price"]
        log = engine_status_coll.find_one()
        
        return log
    
