# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/19 14:58
# @Author  : Gao, Jiezhang (Vic)
# @File    : problem.py

"""
Table of Content:
    Section 1 - problem.get
    Logging Configuration
"""

from modules import base_lib


#####################################
#      Section 1 - problem.get      #
#####################################
# Define a ProblemGet class for calling Zabbix API problem.get, and inherited from MetaClassForQuery from basic_lib.
class ProblemGet(base_lib.MetaClassForQuery):
    def __init__(self, url, token, params):
        super().__init__(url, token, params)
        self.method = 'problem.get'

    # Override the method to meet the requirements of problem.get query.
    def _verify_params(self):
        # problem.get query must have a certain timeframe. Verifying it.
        if not ('eventids' in self.params
                or 'recent' in self.params
                or ('eventid_from' in self.params and 'eventid_till' in self.params)
                or ('time_from' in self.params and 'time_till' in self.params)):
            # No certain timeframe defined. Exit.
            logger.error('No certain timeframe defined in the parameters. Raise an exception')
            raise Exception('You must define a certain timeframe of problem query.')
        else:
            logger.info('Query parameters are verified and look fine.')

    # Other methods are inherited from the Parent class 'MetaClassForQuery'.


#####################################
#       Logging Configuration       #
#####################################
logger = base_lib.configure_logger()
