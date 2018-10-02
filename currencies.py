#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sun Apr  8 10:53:20 2018

@author: joseramon
"""

from selenium import webdriver
import selenium.webdriver.chrome.service as service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import bs4

class ConvertCurrencies:
    
    def __init__(self):
        
        self._root_url = "http://www.google.com/finance?q="
        
        """
        Path where the Selenium driver for your browser is saved.
        Go to http://selenium-python.readthedocs.io/installation.html to search for the
        appropiate driver, copy it to the directory where this script is saved,
        and change 'chromedriver' to match the name of your driver.
        """
        self._path_to_driver = './chromedriver'
        """
        Path where your web browser application is saved. This example is for MacOs, in Windows 7, 8,
        and 10, the path might be ‘C:\Program Files\Google\Chrome\Application’. Search Google if
        you don't know how to find your browser application's path.
        """
        self._path_to_browser = '/Applications/Google Chrome.app'
        
        self._server = None
        self._driver = None


    def start_server_and_driver(self):
        """
        Start the Selenium server and driver and return them as objects.
        =Args=
            self._path_to_driver: The path where the Selenium driver for your browser is saved.
            self._path_to_browser: The path where your browser application is saved.
        """
        
        self._server = service.Service(self._path_to_driver)
        self._server.start()
    
        capabilities = {'chrome.binary': self._path_to_browser}
        self._driver = webdriver.Remote(self._server.service_url, capabilities)
        
    def stop_server_and_driver(self):
        """
        Close the driver and then stop the server.
        =Args=
            self._driver: driver object returned by def start_server_and_driver()
            self._server: server object returned by def start_server_and_driver()
        """
        
        self._driver.close()
        self._server.stop()

    def get_conversion(self, from_currency, to_currency):
        
        self.start_server_and_driver()
        self._driver.get(self._root_url + from_currency + to_currency)
        
        try:
            element = WebDriverWait(self._driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "dDoNo")))
        except Exception as e:
            print(str(e))
        
        content = self._driver.page_source
        soup = bs4.BeautifulSoup(''.join(content), 'lxml')
        
        dirty_price = soup.find("div", {"class" : "dDoNo"}).text
        dirty_price = dirty_price.strip()
        price_in_list = dirty_price.split(" ")
        price = float(price_in_list[0])
        
        return price

"""
convert = ConvertCurrencies()
convert.start_server_and_driver()
print(convert.get_conversion("mxn", "usd"))
print(convert.get_conversion("usd", "mxn"))
convert.stop_server_and_driver()
"""
