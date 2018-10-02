# -*- coding: utf-8 -*-
"""
Created on Fri Apr 06 16:13:20 2018

@author: R1150
"""

from engine import compare_engine

def ticker (bitso_bid, bitso_ask, bitfinex_bid, bitfinex_ask, so_b_q, so_a_q, fin_b_q, fin_a_q):
    ticker_info = {
                   "bitfinex" : {
                               "bid" : bitfinex_bid,
                               "ask" : bitfinex_ask,
                               "bids_quantity" : fin_b_q,
                               "asks_quantity" : fin_a_q
                           },
                   "bitso" : {
                               "bid" : bitso_bid,
                               "ask" : bitso_ask,
                               "bids_quantity" : so_b_q,
                               "asks_quantity" : so_a_q
                           }
               }
    return ticker_info

def wallet(finex_btc, finex_usd, so_btc, so_usd):
    balances = {"type" : "balances",
                "payload" : {
                        "bitfinex" : {"btc" :
                                          {"name" : "btc",
                                          "total" : "N/A",
                                          "locked" : "250",
                                          "available" : str(finex_btc)},
                                      "usd" :
                                          {"name" : "usd",
                                          "total" : "N/A",
                                          "locked" : "500",
                                          "available" : str(finex_usd)}
                                      },
                        "bitso" : {"btc" :
                                          {"name" : "btc",
                                          "total" : "N/A",
                                          "locked" : "250",
                                          "available" : str(so_btc)},
                                   "mxn" :
                                          {"name" : "mxn",
                                          "total" : "N/A",
                                          "locked" : "500",
                                          "available" : str(so_usd)}
                                   }
                              }
                }
    return balances


wallet_y = wallet(4,60,4,60)

print("wallet_y",wallet_y)

print("1",compare_engine._status)

check = compare_engine.check(ticker(10,10,10,10,100,100,100,100),wallet_y)

check = compare_engine.check(ticker(13,10,12,8,100,100,100,100),wallet_y)

print("2",str(check))

buy_sell = compare_engine.buy_sell(ticker(13,10,12,8,100,100,100,100),wallet_y)

print("3",str(buy_sell),buy_sell.transaction)

print("4",compare_engine._status)

wallet_y = compare_engine.make_effective(wallet_y,buy_sell.transaction)

print(wallet_y)

compare_engine.wait()

print("5",compare_engine._status)

check = compare_engine.check(ticker(13,8,13,8,1000,1000,1000,1000),wallet_y)

print("6",str(check))

buy_sell = compare_engine.buy_sell(ticker(13,8,13,8,1000,1000,1000,1000),wallet_y)

print("7",str(buy_sell))

print("8",compare_engine._status)

wallet_y = compare_engine.make_effective(wallet_y,buy_sell.transaction)

print(wallet_y)

compare_engine.wait()

print("5",compare_engine._status)

check = compare_engine.check(ticker(8,8,8,8,1000,1000,1000,1000),wallet_y)

print("6",str(check))







#ticker_x = ticker(11,9,12,8)
#wallet_x = wallet(0,100,10,0)
#
#def make_effective(wallet_curr,transaction = None,withdraw = None):
#    if transaction != None:
#        sell = transaction["payload"]["sell"]
#        buy = transaction["payload"]["buy"]
#        finex_btc = float(wallet_curr["payload"]["bitfinex"]["btc"]["available"])
#        finex_usd = float(wallet_curr["payload"]["bitfinex"]["usd"]["available"])
#        so_btc = float(wallet_curr["payload"]["bitso"]["btc"]["available"])
#        so_usd = float(wallet_curr["payload"]["bitso"]["mxn"]["available"])
#        if sell["exchange"] == "bitfinex":
#            finex_btc_new = finex_btc - sell["amount"] 
#            finex_usd_new = finex_usd + (sell["amount"] * sell["price"])
#            so_btc_new = so_btc + buy["amount"]
#            so_usd_new = so_usd - (buy["amount"] * buy["price"])
#        elif sell["exchange"] == "bitso":
#            finex_btc_new = finex_btc + buy["amount"] 
#            finex_usd_new = finex_usd - (buy["amount"] * buy["price"])
#            so_btc_new = so_btc - sell["amount"]
#            so_usd_new = so_usd + (sell["amount"] * sell["price"])
#            
#        if withdraw != None:
#            _from = withdraw["payload"]["from"]
#            amount = withdraw["payload"]["amount"]
#            if _from == "bitfinex":
#                finex_btc_new = finex_btc_new - amount
#                so_btc_new = so_btc_new + amount
#            elif _from == "bitso":
#                so_btc_new = so_btc_new - amount
#                finex_btc_new = finex_btc_new + amount
#                
#        print(finex_btc_new, finex_usd_new, so_btc_new, so_usd_new)
#            
#        wallet_new = wallet(finex_btc_new, finex_usd_new, so_btc_new, so_usd_new)
#        
#    return wallet_new



#transaction = {'type': 'order', 'payload': {
#        'sell': {
#                'price': 11.0, 'symbol': 'bitcoin', 'type': 'market', 'amount': 5.7272727272727275, 'exchange': 'bitso'}, 
#        'buy': {
#                'price': 8.0, 'symbol': 'bitcoin', 'type': 'exchange limit', 'amount': 4.625, 'exchange': 'bitfinex'}}}
#                
#withdraw = {'type': 'withdrawal', 'payload': {
#        'withdraw_type': 'bitcoin', 'to': 'bitso', 'amount': 0.08556149732620355, 'from': 'bitfinex'}}
#
#
#
#wallet_x = make_effective(wallet_x,transaction,withdraw)
#
#print(wallet_x)

#######################################################################################################################
#print("1",compare_engine._status)
#
#check = compare_engine.check(ticker(100.64,100.34,100.15,100.65))
#
#print("1.5",check)
#
#check = compare_engine.check(ticker(108.11,107.01,110.24,100.12))
#
#print("2",check)
#
#buy_sell = compare_engine.buy_sell(ticker(108.11,107.01,110.24,100.12),wallet(10.235,10000.256,100.246842,10000.24562456))
#
#print("3",compare_engine._status)
#
#print("4",buy_sell)
#
#compare_engine.wait()
#
#print("5",compare_engine._status)
#
#check = compare_engine.check(ticker(100.2562,100.24562,110.874,100.1345))
#
#print("6",check)
#
#buy_sell = compare_engine.buy_sell(ticker(100.2562,100.24562,110.874,100.1345),wallet(10.235,10000.256,100.246842,10000.24562456))
#
#print("7",buy_sell)
#
#print("8",compare_engine._status)
#
#print("9",buy_sell)
#
#compare_engine.wait()
#
#print("10",compare_engine._status)
#
#
#check5 = compare_engine.check(ticker(100.1562,100.14562,100.174,100.1345))
#
#print("11",check5)



####################################################################################################################################################
#check = compare_engine.check(ticker(100, 100, 105.1, 100))
#print("1",check)
#
#print("1.5",compare_engine._status)
#
#check2 = compare_engine.check(ticker(100, 100, 105.1, 100))
#print("2",check2)
#
#buy_sell = compare_engine.buy_sell(ticker(100, 100, 105.1, 100), wallet(10, 1000, 10, 1000))
#print("3",buy_sell)
#
#print("4",compare_engine._status)
#
#compare_engine.response()
#
#print("5",compare_engine._status)
#
#check3 = compare_engine.check(ticker(104.1, 100, 104.1, 100))
#
#print("6",check3)
#
#check4 = compare_engine.check(ticker(103.1, 100, 99, 100))
#
#print("7",check4)
#
#check5 = compare_engine.check(ticker(105.1, 100, 100, 100))
#
#print("8",check5)
#
#buy_sell2 = compare_engine.buy_sell(ticker(105.1, 100, 100, 100), wallet(10, 1000, 10, 1000))
#print("9",buy_sell2)
#
#print("10",compare_engine._status)
#
#compare_engine.response()
#
#print("11",compare_engine._status)
#
#check6 = compare_engine.check(ticker(103.1, 100, 99, 100))
#
#print("12",check6)
#                  
#check7 = compare_engine.check(ticker(104.1, 100, 104.1, 100))
#
#print("13",check7)                                 