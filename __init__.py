


import numpy as np

""" Gets the values for the necessary operations from the ticker and the wallet"""

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
        self.plat1_ave = np.average([self.plat1_bid,self.plat1_ask])
        self.plat2_ave = np.average([self.plat2_bid,self.plat2_ask])
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
    
class Init:
    def __init__(self, ticker, wallet, percentage_balance):
        self._values = GetValues(ticker,wallet)
        
        self._total_usd = self._values.plat1_usd + self._values.plat2_usd + (self._values.plat1_btc*self._values.plat1_bid) + (self._values.plat2_btc*self._values.plat2_bid)
        self._usd_per_wallet = (self._total_usd * percentage_balance * 0.01) / 2
        
        self._plat1_need_have = self._usd_per_wallet - self._values.plat1_usd
        self._plat2_need_have = self._usd_per_wallet - self._values.plat2_usd
        
        print self._plat1_need_have, self._values.plat1_name, self._plat2_need_have, self._values.plat2_name
        
        self.get_plat1_order = self.choose_buy_sell(self._plat1_need_have, self._values.plat1_name, self._values.plats_info[self._values.plat1_name])
        self.get_plat2_order = self.choose_buy_sell(self._plat2_need_have, self._values.plat2_name, self._values.plats_info[self._values.plat2_name])
        
        print self.get_plat1_order, self.get_plat2_order
    
    def choose_buy_sell(self, amount, platform_name, platform):
        if amount < 0:
            order = self.buy(platform_name, abs(amount), platform[1])
        elif amount >= 0:
            order = self.sell(platform_name, abs(amount), platform[0])
        return order
    
    def buy(self, ask_platform, buy_amount, buy_price):
        buy = {"buy" : {"exchange" : ask_platform,
                       "symbol" : "bitcoin",
                       "amount" : buy_amount/buy_price,
                       "price" : buy_price,
                       "type" : "market"}}
        
        return buy
    
    def sell(self, bid_platform, sell_amount, sell_price):
        if bid_platform == "bitfinex":
            type_market = "exchange market"
        else:
            type_market = "market"
        sell = {"sell" : {"exchange" : bid_platform,
                          "symbol" : "bitcoin",
                          "amount" : sell_amount/sell_price,
                          "price" : sell_price,
                          "type" : type_market}}
        return sell
        
    def transaction(self, bid_platform, ask_platform, sell_amount, sell_price, buy_amount, buy_price):
        """ Make a transaction order """
        order_transaction = {"type" : "order",
                       "payload" : {
                            "buy" : {"exchange" : ask_platform,
                                      "symbol" : "bitcoin",
                                      "amount" : buy_amount,
                                      "price" : buy_price,
                                      "type" : "market"},
                            "sell" : {"exchange" : bid_platform,
                                      "symbol" : "bitcoin",
                                      "amount" : sell_amount,
                                      "price" : sell_price,
                                      "type" : "market"} #!!! exchange market cuando es bitfinex!!!
                            }
                        }
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
        
ticker_x = ticker(10, 10, 10, 10, 100, 100, 100, 100)
wallet_x = wallet(5,0,5,100)

init = Init(ticker_x, wallet_x, 60)
        
        
        