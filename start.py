#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sat Apr  7 18:06:32 2018

@author: joseramon
"""

from optparse import OptionParser
from db import DB
from bot import Bot
from engine import Engine
from config import Config
import os
import pprint

import json

KEYS = 'keys.json'

class Start:
    
    def __init__(self, config):
        
        self._db = DB()
        self._engine_status = None
        
        self._bot_status = None
        
        self._bot = None
        self._engine = None
    
        self._config = config
    
    def create_config(self):
        pass
    
    def get_engine_status(self):
        """Get information from db to initialize Engine. Returns json with the following schema:
            
            {"datetime" : year-month-day hour:minute:second (e.g. 2018-04-07 20:35:35.884530),
               "status" : int}
        """
        try:
            self._engine_status = self._db.retrieve_from_engine_status()
            print("\nLast Engine Status:")
            print(self._engine_status)
        except:
            print("\nLast Engine Status:")
            print("None")
            return
        
        return 
    
    def get_total_usd(self):
        try:
            total_usd = self._db.retrieve_last_total_usd()
        except:
            return
        
        return total_usd
    
    def create_engine(self):
        """Initializes engine with the information retrieved from db"""
        
        self.get_engine_status()
        try:
            total_usd = self.get_total_usd()
        except:
            total_usd = None
        
        try:
            status = self._engine_status["status"]
            sell_buy = self._engine_status["sell_buy"]
            balance_order = self._engine_status["balance_order"]
            finish_cycle = self._engine_status["finish_cycle"]
            self._engine = Engine(self._config.thresh, self._config.mid_thresh, \
                                  percentage_balance=self._config.get_percentage(), percentage_sell_buy=self._config.get_extra(), \
                                  status=status, sell_buy=sell_buy, balance_order=balance_order, total_usd=total_usd, finish_cycle=finish_cycle)
        except:
            self._engine = Engine(self._config.thresh, self._config.mid_thresh, \
                                  percentage_balance=self._config.get_percentage(), percentage_sell_buy=self._config.get_extra(), \
                                  total_usd=total_usd)
    
    def get_bot_status(self):
        """Get information from db to initialize Bot. Returns json with the following schema:
            
            {"datetime" : year-month-day hour:minute:second (e.g. 2018-04-07 20:35:35.884530),
               "status" : int,
               "transaction" : dictionary or None,
               "buy_sell" : dictionary or None,
               "withdrawal" : withdrawal or None}
        """
        try:
            self._bot_status = self._db.retrieve_from_bot_status()
            print("\nLast Bot Status:")
            print(self._bot_status)
        except:
            print("\nLast Bot Status:")
            print("None")
            return
        
        return 
    
    
    def create_bot(self):
        """Initializes bot with the information retrieved from db"""
        
        self.get_bot_status()
        
        try:
            status = self._bot_status["status"]
            transaction = self._bot_status["transaction"]
            buy_sell = self._bot_status["buy_sell"]
            withdrawal = self._bot_status["withdrawal"]
            
            self._bot = Bot(self._engine, self._config, status=status, transaction=transaction, \
                            buy_sell=buy_sell, withdrawal=withdrawal)
        except:
            self._bot = Bot(self._engine, self._config)
    
    
    def run(self):
        """Run cryptobot"""
        
        print("Initializing cryptobot! Wahooo!")
        self.create_engine()
        self.create_bot()
        
        print("\nStart Timer! Here we goooooo!")
        self._bot.start_timer()
        
def parser():
    
    usage = "usage: %prog [options]"
    version = "%prog 1.0"
    parser = OptionParser(usage=usage, version=version)
    
    parser.add_option("-t", "--threshold", action="store", dest="threshold", default=5.0, \
                      type="float", help="""Top and bottom threshold for the engine to look for
                      arbitrage oppportunities""")
    parser.add_option("-b", "--balance", action="store", dest="balance_threshold", default=1.0, \
                      type="float", help="""Middle threshold to identify when two exchanges have
                      similar exchange rates that allow us to balance currencies""")
    parser.add_option("-i", "--interval", action="store", dest="interval", default=60, \
                      type="int", help="Interval of time between cycles" )
    parser.add_option("-p", "--percentage", action="store", dest="percentage", default=50, \
                      type="int", help="What percentage of balance should be in cryptocurrencies" )
    parser.add_option("-e", "--extra", action="store", dest="extra", default=30, \
                      type="int", help="""Extra amount of cryptocurrency in the order books that 
                      we will consider before making buys or sells""")

    
    (options, args) = parser.parse_args()
    
    
    with open(os.path.expanduser('~') + '/.keys.json', 'r') as f:
        to_string = f.read()
        keys = json.loads(to_string)
                                    
    config = Config(keys=keys, thresh=options.threshold, mid_thresh=options.balance_threshold, \
                    interval=options.interval, percentage=options.percentage, extra=options.extra)
    
    return config
        
if __name__ == "__main__":
    config = parser()
    start = Start(config)
    
    start.run()

    
