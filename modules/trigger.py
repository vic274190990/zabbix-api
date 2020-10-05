# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/24 21:42
# @Author  : Gao, Jiezhang (Vic)
# @File    : trigger.py

"""
Table of Content:
    Section 1 - trigger.get
    Logging Configuration
"""

from modules import base_lib


#####################################
#      Section 1 - trigger.get      #
#####################################
# Define a TriggerGet class for calling Zabbix API trigger.get, and inherited from MetaClassForQuery from basic_lib.
class TriggerGet(base_lib.MetaClassForQuery):
    def __init__(self, url, token, params):
        super().__init__(url, token, params)
        self.method = 'trigger.get'

    # Other methods are inherited from the Parent class 'MetaClassForQuery'.


#####################################
#       Logging Configuration       #
#####################################
logger = base_lib.configure_logger()
