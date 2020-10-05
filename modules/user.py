# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/19 14:58
# @Author  : Gao, Jiezhang (Vic)
# @File    : user.py

"""
Table of Content:
    Section 1 - user.login
    Section 2 - user.logout
    Logging Configuration
"""

import json
import random

from modules import base_lib


#####################################
#      Section 1 - user.login       #
#####################################
# Define a UserLogin class for calling Zabbix API user.login, and inherited from MetaClassForQuery from basic_lib.
class UserLogin(base_lib.MetaClassForQuery):
    def __init__(self, url):
        # url, the URL of Zabbix API
        self.url = url
        # There is no token before login.
        self.token = None
        # method to call Zabbix APIs.
        self.method = 'user.login'
        # Create an empty dict for params.
        self.params = {}

    def _generate_payload(self):
        # Get the credential either from config file or user input.
        credential = base_lib.ZabbixCredential()
        (username, password) = credential.get_cred()

        # Create the base payload.
        python_payload = {
            'jsonrpc': '2.0',
            'method': self.method,
            'params': {
                'user': username,
                'password': password
            },
            'id': random.randint(0, 1000),
            'auth': self.token
        }

        # Transfer from a python object to a JSON object.
        json_payload = json.dumps(python_payload)
        logger.info('JSON payload generated, content: %s' % json_payload)
        return json_payload

    # Other methods are inherited from the Parent class 'MetaClassForQuery'.


#####################################
#     Section 2 - user.logout      #
#####################################
# Define a UserLogout class for calling Zabbix API user.logout, and inherited from MetaClassForQuery from basic_lib.
class UserLogout(base_lib.MetaClassForQuery):
    def __init__(self, url, token):
        # url, the URL of Zabbix API
        self.url = url
        # token is gotten from login function in another module.
        self.token = token
        # method to call Zabbix APIs.
        self.method = 'user.logout'
        # Create an empty dict for params.
        self.params = []

    def _verify_result_advanced(self, response):
        if not response['result']:
            logger.error('Logout failed. The session may not be released.')
            raise Exception('Logout failed. The session may be not released.')

    # Other methods are inherited from the Parent class 'MetaClassForQuery'.


#####################################
#       Logging Configuration       #
#####################################
logger = base_lib.configure_logger()
