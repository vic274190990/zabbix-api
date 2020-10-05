# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/29 23:02
# @Author  : Gao, Jiezhang (Vic)
# @File    : apiinfo.py

"""
Table of Content:
    Section 1 - apiinfo.version
    Logging Configuration
"""

import random
import json

from modules import base_lib


#####################################
#    Section 1 - apiinfo.version    #
#####################################
# Define a EventGet class for calling Zabbix API event.get, and inherited from MetaClassForQuery from basic_lib.
class ApiinfoVersion(base_lib.MetaClassForQuery):
    def __init__(self, url):
        # url, the URL of Zabbix API
        self.url = url
        # method to call Zabbix APIs.
        self.method = 'apiinfo.version'

    def _generate_payload(self):
        # Create the base payload.
        python_payload = {
            'jsonrpc': '2.0',
            'method': self.method,
            'params': [],
            'id': random.randint(0, 1000),
        }
        # Transfer from a python object to a JSON object.
        json_payload = json.dumps(python_payload)
        logger.info('JSON payload generated, content: %s' % json_payload)
        return json_payload

    # Other methods are inherited from the Parent class 'MetaClassForQuery'.


#####################################
#       Logging Configuration       #
#####################################
logger = base_lib.configure_logger()
