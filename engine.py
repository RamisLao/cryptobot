#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu May 10 19:44:15 2018

@author: FarrasArias
"""

#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sun Apr  1 17:50:57 2018

@author: FarrasArias
"""

import numpy as np
from db import DB
from datetime import datetime

""" Gets the values for the necessary operations from the ticker and the wallet"""
class GetValues:
    def __init__(self, ticker_info = None, wallet_balance = None):
        self.ticker_info = ticker_info
        self.ticker_keys = self.ticker_info.keys()
        self.plat1_name = self.ticker_keys[0]
        self.plat2_name = self.ticker_keys[1]
        self.plat1_bid = self.ticker_info[self.ticker_keys[0]]["bid"]
        self.plat1_ask = self.ticker_info[self.ticker_keys[0]]["ask"]
        self.plat2_bid = self.ticker_info[self.ticker_keys[1]]["bid"]
        self.plat2_ask = self.ticker_info[self.ticker_keys[1]]["ask"]
        self.plat1_bids_quantity = self.ticker_info[self.ticker_keys[0]]["bids_quantity"]
        self.plat1_asks_quantity = self.ticker_info[self.ticker_keys[0]]["asks_quantity"]
        self.plat2_bids_quantity = self.ticker_info[self.ticker_keys[1]]["bids_quantity"]
        self.plat2_asks_quantity = self.ticker_info[self.ticker_keys[1]]["asks_quantity"]
#        self.plat2_info = {self.plat2_name : [self.plat2_bid, self.plat2_ask, self.plat2_btc, self.plat2_usd]}
        #self.plat1_ave = np.average([self.plat1_bid,self.plat1_ask])
        #self.plat2_ave = np.average([self.plat2_bid,self.plat2_ask])
        self.plats_bid_ask = {self.plat1_name : [float(self.plat1_bid), float(self.plat1_ask)],
                           self.plat2_name : [float(self.plat2_bid), float(self.plat2_ask)]}
#        print(wallet_balance)
        if wallet_balance != None:
            self.wallet_balance = wallet_balance["payload"]
            self.dict_plat1 = self.wallet_balance[self.ticker_keys[0]]
            self.dict_plat2 = self.wallet_balance[self.ticker_keys[1]]
            self.plat1_btc, self.plat1_usd = self.find_balance(self.dict_plat1)
            self.plat2_btc, self.plat2_usd = self.find_balance(self.dict_plat2)
            self.plats_info = {self.plat1_name : [float(self.plat1_bid), float(self.plat1_ask), float(self.plat1_btc), float(self.plat1_usd)],
                           self.plat2_name : [float(self.plat2_bid), float(self.plat2_ask), float(self.plat2_btc), float(self.plat2_usd)]}
#            print("plats_info",self.plats_info)
        
        
    def find_balance(self,dict_plat):
        plat_btc = 0
        plat_usd = 0
        for dic in dict_plat:
            if dic == "btc":
                plat_btc = float(dict_plat[dic]["available"])
            elif dic == "usd" or dic == "mxn":
                plat_usd = float(dict_plat[dic]["available"])
        return plat_btc, plat_usd

""" Class to define the stage of the cycle"""
class EngineStatus:
    READY = 0
    ARBITRAGE = 1
    INACTIVE = 2
    WAIT = 3
    BALANCE = 4
    HIGH = True

""" Logic to make comparisons, find arbitrage opportunities and balance moments"""
class Engine:
    """ Decision-making engine to find arbitrage opportunities and create transaction and withdraw orders """
    def __init__(self, high_threshold, mid_threshold, percentage_balance = 60, percentage_sell_buy = 30, status = None, sell_buy = None, balance_order = None, total_usd = None, finish_cycle = False):
        """ Get the information necessary to make decisions.
        
        =args=
            - high_threshold: Percentage. The threshold setting to find arbitrage opportunities. 
            - mid_threshold: Percentage. The threshold setting to find balance opportunities.
            - percentage_balance: Percentage. The ratio of BTC/USD to have at each balance.
            - percentage_sell_buy: Percentage. Security buffer to make sure transactions will be succesful.
        """
        self.high_threshold = high_threshold
        self.mid_threshold = mid_threshold
        self._engine_status = EngineStatus()
        self._db = DB()
        self.sell_buy = sell_buy
        self.balance_order = balance_order
        self.finish_cycle = finish_cycle
        self.percentage = percentage_balance
        self.total_usd = total_usd
        self.p_sell_buy = percentage_sell_buy * 0.01
        
        if status == None:
            self._status = self._engine_status.READY
            self._db.store_to_engine_status(self._status,self.sell_buy,self.balance_order,self.finish_cycle)
            self.log_entry("Type: STATUS, info: " + str(self._status))
            self.log_entry("Type: SELL_BUY ORDERING, info: " + str(self.sell_buy))
            self.log_entry("Type: BALANCE ORDERING, info: " + str(self.balance_order))
            self.log_entry("Type: FINISH CYCLE, info: " + str(self.finish_cycle))
        else:
            self._status = status
            self.log_entry("Type: STATUS, info: " + str(self._status))
            self.log_entry("Type: SELL_BUY ORDERING, info: " + str(self.sell_buy))
            self.log_entry("Type: BALANCE ORDERING, info: " + str(self.balance_order))
            self.log_entry("Type: FINISH CYCLE, info: " + str(self.finish_cycle))

    def log_entry(self, info):
        datetime_now = str(datetime.now())
        with open("./logs/engine_logs.txt", "a") as logs:
            logs.write(datetime_now + " ---- " + info)
            logs.write("\n\n")
            
    def log_stored_items(self, status, sell_buy, balance_order, finish_cycle):
        self.log_entry("Type: STATUS, info: " + str(self._status))
        self.log_entry("Type: SELL_BUY ORDERING, info: " + str(self.sell_buy))
        self.log_entry("Type: BALANCE ORDERING, info: " + str(self.balance_order))
        self.log_entry("Type: FINISH CYCLE, info: " + str(self.finish_cycle))

    def check(self, ticker, wallet):
        """ Function for checking different opportunitites according to the EngineStatus class"""
        self.log_entry("Type: ACTION, info: Check-function started with high %: " + str(self.high_threshold) + " and mid%: " + str(self.mid_threshold))
        self.log_entry("Type: STATUS, info: " + str(self._status))
        
        self.finish_cycle = False
#        print("Sell_Buy", self.sell_buy)
        get_values = GetValues(ticker,wallet)
        current_total_usd = get_values.plat1_usd + get_values.plat2_usd + (get_values.plat1_btc * get_values.plat1_bid) + (get_values.plat2_btc * get_values.plat2_bid)
        percentage_1_2_dummy = ((float(get_values.plat1_bid)/float(get_values.plat2_ask)) * 100) - 100
        percentage_2_1_dummy = ((float(get_values.plat2_bid)/float(get_values.plat1_ask)) * 100) - 100
        self.log_entry("% from " + get_values.plat1_name + " bid to " + get_values.plat2_name + " ask is: " + str(percentage_1_2_dummy))
        self.log_entry("% from " + get_values.plat2_name + " bid to " + get_values.plat1_name + " ask is: " + str(percentage_2_1_dummy))      
        self.log_entry("high threshold - percentage(plat1bid & plat2ask): " + str(self.high_threshold - percentage_1_2_dummy))
        self.log_entry("high threshold - percentage(plat2bid & plat1ask): " + str(self.high_threshold - percentage_2_1_dummy))
        self.log_entry("mid threshold - percentage(plat1bid & plat2ask): " + str(self.mid_threshold - percentage_1_2_dummy))
        self.log_entry("mid threshold - percentage(plat2bid & plat1ask): " + str(self.mid_threshold - percentage_2_1_dummy))
        if self._status == 1:
            """ If a check is called while on arbitrage mode, print the following"""
            print("Currently in arbitrage, no checks allowed")
            return CommDevice(status=None)
        if self._status == 2:
            """ If the state is INACTIVE, do nothing"""
            return CommDevice(status=None)
        elif self._status == 0:
            """ Get the percentages between the bid and ask values of both exchanges"""
            percentage_1_2 = ((float(get_values.plat1_bid)/float(get_values.plat2_ask)) * 100) - 100
            percentage_2_1 = ((float(get_values.plat2_bid)/float(get_values.plat1_ask)) * 100) - 100
#            self.log_entry("% from " + get_values.plat1_name + " bid to " + get_values.plat2_name + " ask is: " + str(percentage_1_2))
#            self.log_entry("% from " + get_values.plat2_name + " bid to " + get_values.plat1_name + " ask is: " + str(percentage_2_1))           
            if percentage_1_2 > self.high_threshold and percentage_1_2 > percentage_2_1:
                """ If the plat1 bid value is higher than the plat2 ask value by the threshold percentage AND it's the best arbitrage option, record the order of the exchanges"""
                if get_values.plat1_btc*get_values.plat1_bid*(1+self.p_sell_buy) <= get_values.plat1_bids_quantity and get_values.plat2_usd*(1+self.p_sell_buy) <= get_values.plat2_asks_quantity:
                    """ If both sell and buy quantities are below the Security buffer, proceed """
                    print "Arbitrage opportinity found from " + str(get_values.plat1_name) + " to " + str(get_values.plat2_name)
                    self._status = self._engine_status.ARBITRAGE
                    self.sell_buy = [get_values.plat1_name, get_values.plat2_name]
                    self._db.store_to_engine_status(self._status,self.sell_buy,self.balance_order,self.finish_cycle)
                    self.log_stored_items(self._status, self.sell_buy, self.balance_order, self.finish_cycle)
                    self.total_usd = current_total_usd
                    self._db.store_last_total_usd(self.total_usd)
                    self.log_entry("Type: DATA, info: " + "Total USD Before transaction: " + str(self.total_usd))
                    return CommDevice(status=self._status)
                else:
                    print("No opportunities found")
                    return CommDevice(status=None)
            elif percentage_2_1 > self.high_threshold and percentage_2_1 > percentage_1_2:
                """ If the plat1 bid value is higher than the plat2 ask value by the threshold percentage AND it's the best arbitrage option, record the order of the exchanges"""
                if get_values.plat2_btc*get_values.plat2_bid*(1+self.p_sell_buy) <= get_values.plat2_bids_quantity and get_values.plat1_usd*(1+self.p_sell_buy) <= get_values.plat1_asks_quantity:
                    """ If both sell and buy quantities are below the Security buffer, proceed """
                    print "Arbitrage opportinity found from " + str(get_values.plat2_name) + " to " + str(get_values.plat1_name)
                    self._status = self._engine_status.ARBITRAGE
                    self.sell_buy = [get_values.plat2_name, get_values.plat1_name]
                    self._db.store_to_engine_status(self._status,self.sell_buy,self.balance_order,self.finish_cycle)
                    self.log_stored_items(self._status, self.sell_buy, self.balance_order, self.finish_cycle)
                    self.total_usd = current_total_usd
                    self._db.store_last_total_usd(self.total_usd)
                    self.log_entry("Type: DATA, info: " + "Total USD Before transaction: " + str(self.total_usd))
                    return CommDevice(status=self._status)
                else:
                    print("No opportunities found")
                    return CommDevice(status=None)
            else:
                print("No opportunities found")
                return CommDevice(status=None)
        elif self._status == 3:
            """ Check if we're on WAIT mode"""
            """ Get the bid and ask values, based on the order of the ARBITRAGE buy_sell_order"""
            plat_x = get_values.plats_bid_ask[self.sell_buy[0]]
            plat_y = get_values.plats_bid_ask[self.sell_buy[1]]
            print ("plats",plat_x[0],plat_x[1], plat_y[0], plat_y[1])
#            print(abs(((plat_y[1]/plat_x[0]) * 100) - 100))
            """ Get the percentage difference to check for another arbitrage or a balance order"""
            percentage = ((plat_x[0]/plat_y[1]) * 100) - 100
            percentage_flip = ((plat_y[0]/plat_x[1]) * 100) - 100
            print("percentages",percentage, percentage_flip)
            if percentage_flip > self.high_threshold:
                """ If the percentage between the bid and ask of the exchanges opposite to the first arbitrage order are higher than the threshold, call for an arbitrage and invert the order"""
                print "Flip arbitrage opportinity found"
                self._status = self._engine_status.ARBITRAGE
                self.sell_buy = [self.sell_buy[1], self.sell_buy[0]]
                self._db.store_to_engine_status(self._status,self.sell_buy,self.balance_order,self.finish_cycle)
                self.log_stored_items(self._status, self.sell_buy, self.balance_order, self.finish_cycle)
                return CommDevice(status=self._status)
            elif abs(percentage) < self.mid_threshold or abs(percentage_flip) < self.mid_threshold:
                """ If any of the percentages is less than the Balance threshold, call for a Balance order"""
                """ Create the balance order """
                balance = self.balance(ticker, wallet)
                """ Get the transaction and withdrawal from the order """
                balance_transaction = balance.transaction["order"]
                balance_withdrawal = balance.transaction["withdrawal"]
                """ Simulate the transaction and widthrawal, get it's values and get the total amount of money after the order """
                wallet_simulation = self.make_effective(wallet, balance_transaction, balance_withdrawal)
                values_simulation = GetValues(ticker,wallet_simulation)
                total_usd_wallet_simulation = values_simulation.plat1_usd + values_simulation.plat2_usd + (values_simulation.plat1_btc * values_simulation.plat1_bid) + (values_simulation.plat2_btc * values_simulation.plat2_bid)
                if total_usd_wallet_simulation >= self.total_usd:                
                    """ If the total amount is less than the original amount before the buy/sell order, do nothing. Otherwise, make the balance """
                    self._status = self._engine_status.BALANCE
                    self._db.store_to_engine_status(self._status,self.sell_buy,self.balance_order,self.finish_cycle)
                    self.log_stored_items(self._status, self.sell_buy, self.balance_order, self.finish_cycle)
                    return CommDevice(status=self._status)
                else:
                    return CommDevice(status=None)
            else:
                return CommDevice(status=None)
            
    def wait(self):
        """ Change the status to wait or ready, depending on the moment in the cycle"""
        if self.finish_cycle == False:
            self._status = self._engine_status.WAIT 
            self._db.store_to_engine_status(self._status,self.sell_buy,self.balance_order,self.finish_cycle)
            self.log_entry("Type: STATUS, info: " + str(self._status))
        else:
            self._status = self._engine_status.READY
            self._db.store_to_engine_status(self._status,self.sell_buy,self.balance_order,self.finish_cycle)
            self.log_entry("Type: STATUS, info: " + str(self._status))
            
    def inactive(self):
        self._status = self._engine_status.INACTIVE
        self._db.store_to_engine_status(self._status,self.sell_buy,self.balance_order,self.finish_cycle)
        self.log_entry("Type: STATUS, info: " + str(self._status))
        
        
    def ready(self):
        """ Change the status to ready"""
        self._status = self._engine_status.READY
        self._db.store_to_engine_status(self._status,self.sell_buy,self.balance_order,self.finish_cycle)
        self.log_entry("Type: STATUS, info: " + str(self._status))

                
    def buy_sell(self, ticker, wallet):
        """ Make a buy_sell_withdraw order once the arbitrage status was found"""    
        if self._status == 1:
            """ Check for status"""
            """ Change the status to INACTIVE"""
#            self._status = self._engine_status.INACTIVE
            """ Get the values of the sell and buy exchange in order to make the transaction order"""
            get_values = GetValues(ticker, wallet)
            print("ordernames",self.sell_buy[0],self.sell_buy[1])
            plat_x = get_values.plats_info[self.sell_buy[0]]
            plat_y = get_values.plats_info[self.sell_buy[1]]
            usd_to_sell_buy = min([plat_x[2]*plat_x[0],plat_y[3]])
            """ Create a transaction dictionary (order)"""
            transaction = self.transaction(self.sell_buy[0], self.sell_buy[1], usd_to_sell_buy/plat_x[0], plat_x[0], usd_to_sell_buy/plat_y[1], plat_y[1])
            """ Get the total number of bitcoins the wallet is supposed to have after the transaction to make a withdraw order"""
#            total_bitcoins = plat_y[2] + plat_x[2]
            """ Make a withdraw order to balance the number of bitcoins"""
            withdraw = self.withdraw(None, None, None)
            self.log_entry("Type: STATUS, info: " + str(self._status))
            self.log_entry("Type: TRANSACTION, info: " + str(transaction))
            self.log_entry("Type: WITHDRAW, info: " + str(withdraw))
            return CommDevice(status=self._engine_status.ARBITRAGE, \
                              transaction={"order" : transaction, "withdrawal" : withdraw})

    def make_effective(self, wallet_curr,transaction = None,withdraw = None):
        """ Simulation engine to check if the balance will be profitable or not.
        
        =args=
            - wallet_curr: the current wallet that will be used for the balance order
            - transaction: The transaction order that will be used.
            - withdraw: The widthraw order that will be used.
        """
        if transaction != None:
            """ If there is a transaction, get the info"""
            try:
                sell = transaction["order"]["payload"]["sell"]
                buy = transaction["order"]["payload"]["buy"]
            except:
                sell = transaction["payload"]["sell"]
                buy = transaction["payload"]["buy"]
            finex_btc = float(wallet_curr["payload"]["bitfinex"]["btc"]["available"])
            finex_usd = float(wallet_curr["payload"]["bitfinex"]["usd"]["available"])
            so_btc = float(wallet_curr["payload"]["bitso"]["btc"]["available"])
            so_usd = float(wallet_curr["payload"]["bitso"]["mxn"]["available"])
            if sell["exchange"] == "bitfinex":
                """ If we will sell bitfinex, make the calculations """
                finex_btc_new = finex_btc - sell["amount"] 
                finex_usd_new = finex_usd + (sell["amount"] * sell["price"])
                so_btc_new = so_btc + buy["amount"]
                so_usd_new = so_usd - (buy["amount"] * buy["price"])
            elif sell["exchange"] == "bitso":
                """ If we will sell bitso, make the calculations """
                finex_btc_new = finex_btc + buy["amount"] 
                finex_usd_new = finex_usd - (buy["amount"] * buy["price"])
                so_btc_new = so_btc - sell["amount"]
                so_usd_new = so_usd + (sell["amount"] * sell["price"])
                
            if withdraw != None:
                """ If there is a widthraw order, get the info """
                _from = withdraw["payload"]["from"]
                amount = withdraw["payload"]["amount"]
                if _from == "bitfinex":
                    """ If the transfer is from bitfinex, calculate the new amount """
                    finex_btc_new = float(finex_btc_new) - float(amount)
                    so_btc_new = float(so_btc_new) + float(amount)
                elif _from == "bitso":
                    """ If the transfer is from bitso, calculate the new amount """
                    so_btc_new = so_btc_new - amount
                    finex_btc_new = finex_btc_new + amount
                    
#            print(finex_btc_new, finex_usd_new, so_btc_new, so_usd_new)
            
            """ Create a new wallet (simulation) to compare """
            wallet_new = self.create_wallet(finex_btc_new, finex_usd_new, so_btc_new, so_usd_new)
            
        return wallet_new

    def balance(self, ticker, wallet):
        """ Get the percentage, the values and total amount of usd in both wallets """
        percentage = self.percentage
        values = GetValues(ticker,wallet)
        print values.plats_info
        total_usd = values.plat1_usd + values.plat2_usd + (values.plat1_btc * values.plat1_bid) + (values.plat2_btc * values.plat2_bid)
        """ Get the amount that each wallet needs to be balanced """
        usd_per_wallet = (total_usd * percentage * 0.01) / 2
        """ Assign an order to the platforms """
        self.balance_order = [values.plat1_name, values.plat2_name]
#        print(values.plat1_name)
        
        if (values.plats_info[self.balance_order[0]][3] - usd_per_wallet) < 0 and (values.plats_info[self.balance_order[1]]) >= 0:
            """ If the plat1 money needed is negative, we need to sell there and buy in plat2, so we assign the correct order of x and y """
            x = 0
            y = 1
        elif (values.plats_info[self.balance_order[0]][3] - usd_per_wallet) >= 0 and (values.plats_info[self.balance_order[1]]) < 0:
            """ If the plat1 money needed is positive, we need to buy there and sell in plat2, so we assign the correct order of x and y """
            x = 1
            y = 0
        
        """ Get the correct values according to the buy and sell platform """
        plata = values.plats_info[self.balance_order[x]] 
        platb = values.plats_info[self.balance_order[y]]
        """ Calculate the usd we're missing to buy and sell to balance """
        plata_usd_to_have = abs(plata[3] - usd_per_wallet)
        platb_usd_to_sell = abs(platb[3] - usd_per_wallet)
                    
#        print("TOHAVENSELL",plata_usd_to_have,platb_usd_to_sell)
        """ Transform to BTC """
        plata_sell_btc = plata_usd_to_have / plata[0]
        platb_buy_btc = platb_usd_to_sell / platb[1]
#        print("SELL;BUY",plata_sell_btc,platb_buy_btc)
        """ Get the ideal BTC to have according to the balanced USDs """
        plata_btc_ideal = ((100 - percentage) * plata_usd_to_have) / (percentage * plata[1])
        platb_btc_ideal = ((100 - percentage) * (platb[3] - platb_usd_to_sell)) / (percentage * platb[1])
#        print("IDEAL",plata_btc_ideal,platb_btc_ideal)
        """ Make the relation a ratio, to apply to the real amount of BTCs owned """
        plata_btc_ratio = plata_btc_ideal / (plata_btc_ideal + platb_btc_ideal)
        platb_btc_ratio = 1 - plata_btc_ratio
#        print("RATIOS",plata_btc_ratio,platb_btc_ratio)
        """ Get the real BTCs we need to have """
        plata_new_btc = plata[2] - plata_sell_btc
        platb_new_btc = platb[2] + platb_buy_btc
#        print("btcs",plata_new_btc,platb_new_btc)
        plata_ideal_btc = (plata_new_btc + platb_new_btc) * plata_btc_ratio
        platb_ideal_btc = (plata_new_btc + platb_new_btc) * platb_btc_ratio
        print(plata_ideal_btc, platb_ideal_btc)
        """ according to the BTCs needed, make the correct transfer order"""
        if plata_new_btc < plata_ideal_btc:
            transfer_platb_plata = plata_ideal_btc - plata_new_btc
            withdraw = self.withdraw(self.balance_order[1],self.balance_order[0],transfer_platb_plata)
        elif platb_new_btc < platb_ideal_btc:
            transfer_plata_platb = platb_ideal_btc - platb_new_btc
            withdraw = self.withdraw(self.balance_order[0],self.balance_order[1],transfer_plata_platb)
        else:
            withdraw = self.withdraw(self.balance_order[0],self.balance_order[1],0)

        """ Make the transaction order """            
        transaction = self.transaction(self.balance_order[0],self.balance_order[1],plata_sell_btc,plata[0],platb_buy_btc,platb[1])
        
        self.finish_cycle = True
        self.log_entry("Type: STATUS, info: " + str(self._status))
        self.log_entry("Type: TRANSACTION, info: " + str(transaction))
        self.log_entry("Type: WITHDRAW, info: " + str(withdraw))
        self.log_entry("Type: FINISH CYCLE, info: " + str(self.finish_cycle))
        return CommDevice(transaction={"order" : transaction, "withdrawal" : withdraw})
            

    def create_wallet(self, finex_btc, finex_usd, so_btc, so_usd): 
        """ create a wallet. Used to make simulations """
        balances = {"type" : "balances",
                    "payload" : {
                            "bitfinex" : {"btc" :
                                              {"name" : "btc",
                                              "total" : str(finex_btc),
                                              "locked" : "250",
                                              "available" : str(finex_btc)},
                                          "usd" :
                                              {"name" : "usd",
                                              "total" : str(finex_usd),
                                              "locked" : "500",
                                              "available" : str(finex_usd)}
                                          },
                            "bitso" : {"btc" :
                                              {"name" : "btc",
                                              "total" : str(so_btc),
                                              "locked" : "250",
                                              "available" : str(so_btc)},
                                       "mxn" :
                                              {"name" : "mxn",
                                              "total" : str(so_usd),
                                              "locked" : "500",
                                              "available" : str(so_usd)}
                                       }
                                  }
                    }
        return balances
    
    def transaction(self, bid_platform, ask_platform, sell_amount, sell_price, buy_amount, buy_price):
        """ Make a transaction order """
        order_transaction = {"type" : "order",
                       "payload" : {
                            "buy" : {"exchange" : ask_platform,
                                      "symbol" : "bitcoin",
                                      "amount" : buy_amount},
                            "sell" : {"exchange" : bid_platform,
                                      "symbol" : "bitcoin",
                                      "amount" : sell_amount}
                            }
                        }
        if bid_platform == "bitfinex":
            order_transaction["payload"]["buy"]["type"] = "market"
            order_transaction["payload"]["sell"]["type"] = "exchange market"
            order_transaction["payload"]["sell"]["price"] = np.random.randint()
        else:
            order_transaction["payload"]["buy"]["type"] = "exchange market"
            order_transaction["payload"]["sell"]["type"] = "market"
            order_transaction["payload"]["buy"]["price"] = np.random.randint()

        return order_transaction
    
    def withdraw(self, from_account, to_account, total_amount_to_split):
        """ Make a withdraw order """
        if total_amount_to_split != None:
            amount = str(total_amount_to_split / 2)
            from_account = str(from_account)
            to_account = str(to_account)
        else:
            amount = None
        withdrawal_transaction = {"type" : "withdrawal",
                                  "payload" : {
                                          "from" : from_account,
                                          "to" : to_account,
                                          "withdraw_type" : "bitcoin",
                                          "amount" : amount
                                }}       
        return withdrawal_transaction   

class CommDevice:
    def __init__(self, status=None, transaction=None):
        self.status = status
        self.transaction = transaction
        
    def __str__(self):
        return "Status: " + str(self.status) + " " + "Transaction: " + str(self.transaction)
                
