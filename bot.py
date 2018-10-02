#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 25 13:52:47 2018

@author: joseramon
"""

from threading import Timer
import logging
from engine import EngineStatus
import time
import requests
import json
import datetime
import random
import pprint


from mainAPI import Client, TradeClient
from db import DB

logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-10s) %(message)s',
                    )

CURRENCY_LAYER_KEY = "466f3f063b0d7d673b08593a04a367c4"
CL_GET = "http://apilayer.net/api/live?access_key=" + CURRENCY_LAYER_KEY + "&currencies=MXN"

LOGS = "./logs/bot_logs.txt"

class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer     = None
        self.interval   = interval
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False

class BotStatus:
    TICKER = 0
    ACTIVE = 1
    TRANSACTION = 2
    ORDER = 3
    WAIT_FOR_ORDER = 4
    WITHDRAWAL = 5
    WAIT_FOR_WITHDRAWAL = 6
    END = 7

class Bot:
    """Bot to automate the process of arbitrage. It calls the Main API to get tickers;
    then, sends them to Processing; if Processing finds a possible action, bot then
    sends that action to Main API and receives the response of the action."""
    
    def __init__(self, engine, config, status=None, transaction=None, \
                 buy_sell=None, withdrawal=None):
        
        #Config instance
        self._config = config
        
        #Interval of time in which to ask for tickles
        self._interval = self._config.interval
        
        #Status of Bot and Engine
        self._botStatus = BotStatus()
        self._status = status
        self._engine_status = EngineStatus()
        #Instance of Engine for this run
        self._engine = engine
        
        #Dictionaries related to transactions and their outcomes
        self._transaction = transaction
        self._buysell_response = buy_sell
        self._withdrawal_response = withdrawal
        
        #Db instance to store information about Bot
        self._db = DB()
        
        #Current order books
        self._order_books = None
        self._fake_ticker = None
        
        #Current price of mxn to usd
        self._mxn_to_usd = None
        
    
    def start_timer(self):
        self._timer = RepeatedTimer(self._interval, self.check_for_opportunities)
        
    def stop_timer(self):
        self._timer.stop()
        
    def restart_timer(self):
        self._timer.start()
        
    def change_interval(self, new_interval):
        self._interval = new_interval
        self._timer.interval = self._interval
    
    def check_for_opportunities(self):
        """Every self._interval seconds, asks for tickers from all the exchanges in
        self._config._exchanges and send them to self._engine to check for arbitrage or balance
        opportunities. If an opportunity is found, execute the transaction."""
        
        self.stop_timer()
        
        if self._status == self._botStatus.TICKER or self._status == self._botStatus.ACTIVE \
        or self._status == None:
            self.start_cycle()
        elif self._status == self._botStatus.TRANSACTION or \
        (self._status == self._botStatus.ORDER and self._buysell_response == None):
            self._transaction = None
            self.start_cycle()
        elif self._status == self._botStatus.ORDER and self._buysell_response != None:
            self._status = self._botStatus.WAIT_FOR_ORDER
            self.wait_for_order()
        elif self._status == self._botStatus.WAIT_FOR_ORDER:
            self.wait_for_order()
        elif self._status == self._botStatus.WITHDRAWAL and self._withdrawal_response == None:
            self.execute_withdrawal()
        elif self._status == self._botStatus.WITHDRAWAL and self._withdrawal_response != None:
            self._status = self._botStatus.WAIT_FOR_WITHDRAWAL
            self.wait_for_withdrawal()
        elif self._status == self._botStatus.WAIT_FOR_WITHDRAWAL:
            self.wait_for_withdrawal()
        elif self._status == self._botStatus.END:
            self.end_cycle()
                
    def start_cycle(self):
        """Start the cycle getting current tickers and checking for opportunities"""
        
        print("\nWelcome to the beginning of a Cycle. Hold on tight!\n")
        self._status = self._botStatus.TICKER
        
        self.get_order_books()
        self.get_price_mxn_to_usd() #Only 10 times per day
        self._fake_ticker = self.orders_to_tickers()
        balances_response = self.get_balances()
        
        opportunities = self._engine.check(self._fake_ticker, balances_response)

        if opportunities.status == None:
            self.store_status_to_db()
            print("""Current prices ("""+str(datetime.datetime.now())+""") : \n\n
                  bitfinex_bid = """ + str(self._fake_ticker['bitfinex']['bid']) + """\n\n
                  bitfinex_ask = """ + str(self._fake_ticker['bitfinex']['ask']) + """\n\n
                  bitso_bid = """ + str(self._fake_ticker['bitso']['bid']) + """\n\n
                  bitso_ask = """ + str(self._fake_ticker['bitso']['ask']) + """\n\n""")
            print(self.no_opportunity())
            time.sleep(60)
            self.restart_timer()
            
            return
        
        else:
            self._status = self._botStatus.ACTIVE
            self.store_status_to_db()
            self.opportunity_found(opportunities, balances_response)
            
    def opportunity_found(self, opportunities, balances_response):
        """Get the cient' balances and a new ticker to ask for a transaction order.
        
        =args=
            - opportunities: dictionary sent by compare engine that tells us if an
                             opportunity was found.
            - balances_response: dictionary containing balances details from the user's
                            account.
        """                
        self._status = self._botStatus.TRANSACTION
        self.store_status_to_db()
        self.get_transactions(opportunities, balances_response)

    def get_transactions(self, opportunities, balances_response):
        """If an opportunity was found, ask compare engine for the transaction details
        in order to execute them.
        
        =args=
            - opportunities: dictionary sent by compare engine that tells us if an
                            opportunity was found.
            - balances_response: dictionary containing balances details from the user's
                            account.
            - new_ticker: dictionary containing current info about the cryptocurrencies'
                            market.
        """
        if opportunities.status == self._engine_status.ARBITRAGE:
            print("\nAn opportunity for arbitrage was encountered!")
            
            self._transaction = self._engine.buy_sell(self._fake_ticker, balances_response).transaction
            
        elif opportunities.status == self._engine_status.BALANCE:
            print("\nAn opportunity for balance was encountered!")
            
            self._transaction = self._engine.balance(self._fake_ticker, balances_response).transaction
            
        print("\nWe will humbly execute the following transaction:")
        print(self._transaction)
        self.transaction_to_mxn()
        self._status = self._botStatus.ORDER
        self.store_status_to_db()
        self.execute_order()
        
    def execute_order(self, balances_response):
        """Make a buy/sell order to mainAPI"""
        
        try:
            client_buysell = TradeClient(self._config.get_keys(), self._config, self._transaction["order"])
            self._buysell_response = client_buysell.run()
        except Exception as e:
            self.store_error(e)
            
            return
        
        self._engine.inactive()
        
        self._db.store_to_balances(balances_response)
        self.store_to_log("None", "Current Transaction", self._transaction)
        self.store_to_log(balances_response, "Order executed", self._buysell_response)
        
        print("\nOrder executed! Details below:")
        print(self._buysell_response)
        
        self._status = self._botStatus.WAIT_FOR_ORDER
        self.store_status_to_db()
        self.wait_for_order()
        
    def wait_for_order(self):
        """Wait to confirm the buy/sell order"""
        
        client = TradeClient(self._config.get_keys(), self._config)
        transaction = {"type" : "order_status",
                       "exchange" : None,
                       "id" : None}
        
        bitfinex_done = False
        bitso_done = False
        
        try:
            bitfinex_id = int(self._buysell_response["bitfinex"][self._config.get_ids()["bitfinex"]])
            bitso_id = self._buysell_response["bitso"][self._config.get_ids()["bitso"]]
        except Exception as e:
            self.store_error(e)
            
            return
        
        print("\nWait until order completion is confirmed. You can do the following while you wait:")
        print(self.while_you_wait())
        
        response = {"bitfinex" : None, "bitso" : None}
        while bitfinex_done == False and bitso_done == False:
            
            #Check Bitfinex Order
            if bitfinex_done == False:
                transaction["exchange"] = "bitfinex"
                transaction["id"] = bitfinex_id
                client.change_transaction(transaction)
                response["bitfinex"] = client.check_status()
                try:
                    if float(response["bitfinex"]["remaining_amount"]) == 0.0:
                        bitfinex_done = True
                except Exception as e:
                    self.store_error(e)
                    
                    return
            
            #Check Bitso Order
            if bitso_done == False:
                transaction["exchange"] = "bitso"
                transaction["id"] = bitso_id
                client.change_transaction(transaction)
                response["bitso"] = client.check_status()
                try:
                    if response["bitso"]["status"] == "completed":
                        bitso_done = True
                except Exception as e:
                    self.store_error(e)
                    
                    return
            
            time.sleep(60)
            
        balances_response = self.get_balances()
        self._db.store_to_balances(balances_response)
        self.store_to_log(balances_response, "Order Confirmed", response)
        
        print("\nOrder completed! Blink twice to continue!")
        
        self._status = self._botStatus.WITHDRAWAL
        self.store_to_buysell_log(self._transaction["order"], response)
        self.store_status_to_db()
        self.execute_withdrawal()

    def execute_withdrawal(self):        
        """Make a withdrawal order to mainAPI"""
        
        do_withdrawals = False #!!! True if we want to allow withdrawals
        if not do_withdrawals:
            self.end_cycle()
        else:
            if self._transaction["withdrawal"]["payload"]["from"] == None:
                self.end_cycle()
            else:
                self._transaction["withdrawal"]["payload"]["addresses"] = self.get_addresses(self._config.get_cryptocurrencies())
                
                try:
                    client_withdrawal = TradeClient(self._config.get_keys(), self._config, self._transaction["withdrawal"])
                    self._withdrawal_response = client_withdrawal.run()
                except Exception as e:
                    self.store_error(e)
                    
                    return
                    
                try:
                    self._withdrawal_response = self._withdrawal_response[0]
                except:
                    pass
                
                self.store_to_log("None", "Withdrawal executed", self._withdrawal_response)
                
                print("\nWithdrawal executed! Details below:")
                print(self._withdrawal_response)
                
                self._status = self._botStatus.WAIT_FOR_WITHDRAWAL
                self.store_status_to_db()
                self.wait_for_withdrawal()
        
    def wait_for_withdrawal(self):
        """Wait to confirm the withdrawal order"""
        
        client = TradeClient(self._config.get_keys(), self._config)
        withdrawal_from = self._transaction["withdrawal"]["payload"]["from"]
        withdrawal_type = self._transaction["withdrawal"]["payload"]["withdraw_type"]
        transaction = {"type" : "withdrawal_status",
                       "exchange" : withdrawal_from,
                       "withdrawal_type" : withdrawal_type,
                       "id" : None}
        
        to = None
        
        try:
            if withdrawal_from == "bitfinex":
                transaction["id"] = self._withdrawal_response["withdrawal_id"]
                to = "bitso"
            elif withdrawal_from == "bitso":
                transaction["id"] = self._withdrawal_response["wid"]
                to = "bitfinex"
        except Exception as e:
            self.store_error(e)
            
            return
        
        current_to_balance = self.get_balances()["payload"][to]["btc"]["total"]
        try:
            current_to_balance = float(current_to_balance)
        except Exception:
            pass
        
        withdrawal_done = False
        
        client.change_transaction(transaction)
        
        print("\nWait until withdrawal is completed. You can do the following while you wait:")
        print(self.while_you_wait())
        
        response = None
        while not withdrawal_done:
            response = client.check_status()
            
            print("\nresponse:")
            print(response)
            
            try:
                if withdrawal_from == "bitfinex":
                    if response[0]["id"] == transaction["id"] and response[0]["status"] == "COMPLETED":
                        response = response[0]
                        withdrawal_done = True
                elif withdrawal_from == "bitso":
                    if response["status"] == "complete":
                        withdrawal_done = True
            except Exception as e:
                self.store_error(e)
                
                return
                    
            time.sleep(60)
            
        withdrawal_confirmed = False
        while not withdrawal_confirmed:
            
            new_to_balance = self.get_balances()["payload"][to]["btc"]["total"]
            try:
                new_to_balance = float(new_to_balance)
            except Exception:
                pass
            
            if current_to_balance != new_to_balance:
                withdrawal_confirmed = True
                
            time.sleep(60)
        
        balances_response = self.get_balances()
        self._db.store_to_balances(balances_response)
        self.store_to_log(balances_response, "Withdrawal Confirmed", response)
        
        print("\nWithdrawal completed! Sing 'Aleluya' while you juggle a baby to continue!")
        
        self._status = self._botStatus.END
        self.store_to_withdrawal_log(self._transaction["withdrawal"], response)
        self.store_status_to_db()
        self.end_cycle()
        
    def end_cycle(self):
        """Tell compare engine that we are done, reset variables and restart the cycle"""
        
        self._engine.wait()
        self._transaction = None
        self._buysell_response = None
        self._withdrawal_response = None
        self._status = self._botStatus.TICKER
        self.store_status_to_db()
        self.get_price_mxn_to_usd()
        
        print("\nWe are pleased to announce that this cycle has ended. See you in the next one!")
        
        self.restart_timer()
            
    def get_tickers(self):
        """Ask mainAPI for current tickers"""
        
        client = Client(self._config)
        tickers = client.ticker(self._config.get_cryptocurrencies())
        return tickers
    
    def get_order_books(self):
        """Ask mainAPI for current order books"""
        
        client = Client(self._config)
        self._order_books = client.order_books(self._config.get_cryptocurrencies())
        
        return
    
    def orders_to_tickers(self):
        """Converts order_books to a format similar to tickers to pass them to engine.py"""
        
        fake_ticker = {
                    "bitfinex" : {
                                "bid" : 0,
                                "ask" : 0,
                                "bids_quantity" : 0,
                                "asks_quantity" : 0
                            },
                    "bitso" : {
                                "bid" : 0,
                                "ask" : 0,
                                "bids_quantity" : 0,
                                "asks_quantity" : 0
                            }
                }
                    
        order_books = self._order_books
        
        fake_ticker["bitfinex"]["bid"] = order_books["bitfinex"]["bids"][-1]["price"]
        fake_ticker["bitfinex"]["ask"] = order_books["bitfinex"]["asks"][-1]["price"]
        
        fake_ticker["bitso"]["bid"] = float(order_books["bitso"]["bids"][-1]["price"]) * self._mxn_to_usd
        fake_ticker["bitso"]["ask"] = float(order_books["bitso"]["asks"][-1]["price"]) * self._mxn_to_usd
        
        bitfinex_bids_quantity = 0
        for bid in order_books["bitfinex"]["bids"]:
            bitfinex_bids_quantity += bid["amount"]
            
        fake_ticker["bitfinex"]["bids_quantity"] = bitfinex_bids_quantity
        
        bitfinex_asks_quantity = 0
        for bid in order_books["bitfinex"]["asks"]:
            bitfinex_asks_quantity += bid["amount"]
            
        fake_ticker["bitfinex"]["asks_quantity"] = bitfinex_asks_quantity
        
        bitso_bids_quantity = 0
        for bid in order_books["bitso"]["bids"]:
            bitso_bids_quantity += bid["amount"]
            
        fake_ticker["bitso"]["bids_quantity"] = bitso_bids_quantity
        
        bitso_asks_quantity = 0
        for bid in order_books["bitso"]["asks"]:
            bitso_asks_quantity += bid["amount"]
            
        fake_ticker["bitso"]["asks_quantity"] = bitso_asks_quantity
        
        return fake_ticker
    
    """
    def get_price_mxn_to_usd(self):
        Get current price of mxn to usd according to Google
        
        convert = ConvertCurrencies()
        convert.start_server_and_driver()
        self._mxn_to_usd = convert.get_conversion("mxn", "usd")
        convert.stop_server_and_driver()
    """
    
    def get_price_mxn_to_usd(self, forced=False):
        """Get current price of mxn to usd according to Currency Layer's 
        http://apilayer.net/api/live.
        
        =args=
            - forced: When True, get new price regardless of the last time we got it.
        """
        
        current_time = datetime.datetime.now()
        current_day = current_time.day
        
        if forced == False:
            try:
                saved_time = self._db.retrieve_from_mxnusd_price()["time"]
                
                if current_day != saved_time:
                    data = requests.get(CL_GET)
                    data_text = json.loads(data.text)
                    self._mxn_to_usd = round(1.0 / data_text["quotes"]["USDMXN"], 8)
                    self._db.store_to_mxnusd_price(current_day, self._mxn_to_usd)
            
                else:
                    self._mxn_to_usd = self._db.retrieve_from_mxnusd_price()["price"]
                    
                return
            
            except Exception:
                data = requests.get(CL_GET)
                data_text = json.loads(data.text)
                self._mxn_to_usd = round(1.0 / data_text["quotes"]["USDMXN"], 8)
                self._db.store_to_mxnusd_price(current_day, self._mxn_to_usd)
                
                return
        
        else:
            data = requests.get(CL_GET)
            data_text = json.loads(data.text)
            self._mxn_to_usd = round(1.0 / data_text["quotes"]["USDMXN"], 8)
            self._db.store_to_mxnusd_price(current_day, self._mxn_to_usd)
        
            return
    
    def get_balances(self):
        """Ask mainAPI for current balances"""
        
        client_balances = TradeClient(self._config.get_keys(), self._config)
        balances_response = client_balances.run()
        
        new_available = round(balances_response["payload"]["bitso"]["mxn"]["available"] * self._mxn_to_usd, 8)
        new_locked = round(balances_response["payload"]["bitso"]["mxn"]["locked"] * self._mxn_to_usd, 8)
        new_total = round(balances_response["payload"]["bitso"]["mxn"]["total"] * self._mxn_to_usd, 8)
        
        balances_response["payload"]["bitso"]["mxn"]["available"] = new_available
        balances_response["payload"]["bitso"]["mxn"]["locked"] = new_locked
        balances_response["payload"]["bitso"]["mxn"]["total"] = new_total
        
        return balances_response
    
    def get_addresses(self, currency):
        """Get deposit addresses for Bitso and Bitfinex.
        
        =args=
            - currency: Name of cryptocurrency that we want to withdraw and deposit.
        """
        
        transaction = {"type" : "addresses",
                       "currency" : currency}
        
        client = TradeClient(self._config.get_keys(), self._config, transaction=transaction)
        addresses_response = client.run()
        
        parsed_response = {"bitfinex" : addresses_response["payload"]["bitfinex"]["address"],
                           "bitso" : addresses_response["payload"]["bitso"]["payload"]["account_identifier"]}
        
        return parsed_response
    
    def transaction_to_mxn(self):
        """Take self._transaction and convert bitso's amount to mxn"""
        
        payload = self._transaction["order"]["payload"]
        if payload["buy"]["exchange"] == "bitso":
            new_amount = round(payload["buy"]["amount"] / self._mxn_to_usd, 8)
            self._transaction["order"]["payload"]["buy"]["amount"] = new_amount
        elif payload["sell"]["exchange"] == "bitso":
            new_amount = round(payload["sell"]["amount"] / self._mxn_to_usd, 8)
            self._transaction["order"]["payload"]["sell"]["amount"] = new_amount
            
        return
    
    def store_status_to_db(self):
        self._db.store_to_bot_status(self._status, self._transaction, \
                                         self._buysell_response, self._withdrawal_response)

    def store_to_buysell_log(self, transaction, response):
        complete_log = {"buysell_log" : {"transaction" : transaction,
                                            "response" : response}}
        self._db.store_to_buysell_log(complete_log)
        
    def store_to_withdrawal_log(self, transaction, response):
        complete_log = {"withdrawal_log" : {"transaction" : transaction,
                                            "response" : response}}
        
        self._db.store_to_withdrawal_log(complete_log)
        
    def store_to_log(self, balances, status, data):
        
        log = """----------------------------------------\n\n""" + datetime.datetime.now() + """\n\n
            Current balances: """ + str(balances) + """\n\n    
            Status: """ + str(status) + """\n\n
            Data: """ + str(data) + """\n\n"""
        
        with open(LOGS, 'a') as logs:
            logs.write(log)
            
    def store_error(self, error):
        self.store_to_log("None", "Error", error)
        
    def while_you_wait(self):
        
        options = ["\nHop on a headless horse and ride to Wonderland!\n",
                   "\nListen to your own nails growing!\n",
                   "\nDance with all of the might of a tiny butterfly!\n",
                   "\nTerraform the Sun!\n",
                   "\nBuilt a human-like robot that waits in your stead!\n",
                   "\nGoogle images of 'blue waffle'! No, wait, better don't.\n",
                   "\nScream with all the strength of your lungs: Ziplydifaduk!!!\n",
                   "\nStart a rock band named 'Crypto-booty'!\n",
                   "\nLook at me. No, seriously: LOOK... AT... ME!\n"
                   "\nWaaaaaaaaaaaaait foooor iiiiiiiiiit...\n"
                   "\nDrink water from the toilet while your dog watches!\n"]
        
        return random.choice(options)
    
    def no_opportunity(self):
        
        options = ["\nNo opportunities found... Bad luck, man... Restart Timer, then...\n",
                   "\nNot today... n o t ... t o d a y ...\n",
                   "\nMaybe we'll get lucky next time...\n",
                   "\nNothing?! Really?!?!\n",
                   "\nI'm sorry... We found nothing...\n",
                   "\nMaybe next time?\n"]
        
        return random.choice(options)

