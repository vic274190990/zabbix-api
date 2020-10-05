# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/19 14:58
# @Author  : Gao, Jiezhang (Vic)
# @File    : event.py

"""
Table of Content:
    Section 1 - event.get
    Logging Configuration
"""

from modules import base_lib


#####################################
#      Section 1 - problem.get      #
#####################################
# Define a EventGet class for calling Zabbix API event.get, and inherited from MetaClassForQuery from basic_lib.
class EventGet(base_lib.MetaClassForQuery):
    def __init__(self, url, token, params):
        super().__init__(url, token, params)
        self.method = 'event.get'

    # Override the method to meet the requirements of event.get query.
    def _verify_params(self):
        # event.get query must have a certain timeframe. Verifying it.
        if not ('eventids' in self.params
                or ('eventid_from' in self.params and 'eventid_till' in self.params)
                or ('time_from' in self.params and 'time_till' in self.params)):
            # No certain timeframe defined. Exit.
            logger.error('No certain timeframe defined in the parameters. Raise an exception')
            raise Exception('You must define a certain timeframe of event query.')
        else:
            logger.info('Query parameters are verified and look fine.')

    # Other methods are inherited from the Parent class 'MetaClassForQuery'.


#####################################
#       Logging Configuration       #
#####################################
logger = base_lib.configure_logger()
