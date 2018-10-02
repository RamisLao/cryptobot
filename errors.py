#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sat May 12 13:13:18 2018

@author: joseramon
"""

class Error(Exception):
    pass

class APIError(Error):
    
    def __init__(self, message):
        self._message = message