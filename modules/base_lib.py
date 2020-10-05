# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/19 14:58
# @Author  : Gao, Jiezhang (Vic)
# @File    : base_lib.py

"""
Table of Content:
    Section 1 - Miscellaneous Funcs
    Section 2 - Logger Configurator
    Section 3 - Zabbix URL
    Section 4 - Zabbix Credential
    Section 5 - Connection with Zabbix
    Section 6 - Meta Class of Query
    Logging Configuration
"""

import logging.config
import json
import http.client
import ssl
import random
import os
import time
import datetime
import re

import yaml


#####################################
#  Section 1 - Miscellaneous Funcs  #
#####################################
# Open YAML configuration file and parse it to a Python dict.
def get_yaml():
    with open('./zabbix-api-config.yml', mode='r') as conf_file:
        parsed_result = yaml.load(conf_file.read(), Loader=yaml.SafeLoader)
    return parsed_result


# Verify if user input time is valid.
def verify_time(time_to_verify):
    try:
        time.strptime(time_to_verify, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return False
    else:
        return True


# Compare t1 and t2, which is later/
def compare_time(t1, t2):
    if t1 > t2:
        return True
    else:
        return False


# Calculate time difference
def calculate_time_delta(t1, t2):
    start_time = datetime.datetime.fromtimestamp(int(t1))
    logger.debug('t1 = %s' % start_time)
    end_time = datetime.datetime.fromtimestamp(int(t2))
    logger.debug('t2 = %s' % end_time)
    time_delta = (end_time - start_time).seconds
    logger.info('time delta = %s' % time_delta)
    return time_delta


# Calculate from the amount of secs to readable time in the format like "[w]d [x]h [y]m [z]s".
def convert_to_readable_time(secs):
    mins, sec = divmod(secs, 60)
    if mins > 0:
        hrs, mins = divmod(mins, 60)
        if hrs > 0:
            days, hr = divmod(hrs, 24)
            if days > 0:
                time_readable = str(days) + 'd ' + str(hrs) + 'h ' + str(mins) + 'm ' + str(sec) + 's'
            else:
                time_readable = str(hrs) + 'h ' + str(mins) + 'm ' + str(sec) + 's'
        else:
            time_readable = str(mins) + 'm ' + str(sec) + 's'
    else:
        time_readable = str(sec) + 's'
    return time_readable


class CsvFilename:
    @staticmethod
    def _verify_filename_suffix(input_filename):
        # Verify if the filename ends up with '.csv'.
        if re.search(r'/*\.csv', input_filename, re.I) is None:
            logger.error('Filename suffix verification failed. Content verified: %s' % input_filename)
            return False
        else:
            logger.info('Filename suffix verification succeeded. Content verification %s' % input_filename)
            return True

    @staticmethod
    def _process_windows_path(input_filename):
        if '\\' in input_filename:
            logger.info('Found character \\ in user input filename %s . To be dealt with.' % input_filename)
            input_filename = 'r\'' + input_filename + '\''
            return input_filename
        else:
            return input_filename

    def user_input(self):
        input_filename = input('Output filename:\n'
                               'e.g. csv1.csv, C:\\Download\\csv1.csv, /tmp/csv1.csv, ../csv1,csv\n'
                               'If you do not specify the path, it will be put in the current fold.\n')
        # Verify suffix filename.
        while self._verify_filename_suffix(input_filename) is False:
            input_filename = input('Invalid filename suffix. The suffix should end with .csv!\n'
                                   'Output filename:\n'
                                   'e.g. csv1.csv, C:\\Download\\csv1.csv, /tmp/csv1.csv, ../csv1,csv\n'
                                   'If you do not specify the path, it will be put in the current fold.\n')
        # Handle Windows path.
        input_filename = self._process_windows_path(input_filename)
        return input_filename


#######################################
#   Section 2 - Logger Configurator   #
#######################################
# Define a function to configure the logger for respective modules.
def configure_logger():
    # Open the api-logging file to get the dict of logging configuration.
    with open('./zabbix-api-logging.yml', mode='r') as _logging_conf_file:
        logging_conf = yaml.load(_logging_conf_file.read(), Loader=yaml.SafeLoader)
    # Open the api-config file to get the dict of logger configuration.
    _logger_conf = get_yaml()['logger_conf']
    # Get the full name (path and filename) of log file, and put it into the dict of logging configuration.
    logging_conf['handlers']['timedRotatingFileHandler']['filename'] = _logger_conf['log_file_fullname']
    # Define the logger names to be used in the respective modules.
    logger_name = _logger_conf['loggers'][str(os.path.basename(__file__)).replace('.py', '')]
    # Configure the logger
    logging.config.dictConfig(logging_conf)
    my_logger = logging.getLogger(logger_name)
    return my_logger


#######################################
#       Section 3 - Zabbix URL        #
#######################################
# Define a class ZabbixURL to get the host and path of Zabbix API.
class ZabbixURL:
    # Verify if the Zabbix API URL is valid.
    @staticmethod
    def _verify_url(url):
        if ((url.find('http://') == -1 and url.find('https://') == -1)
                or (url.find('/api_jsonrpc.php') == -1)):
            logger.error('The URL %s is invalid.' % url)
            return False
        else:
            logger.info('The URL %s is valid. Going ahead.' % url)
            return True

    # Try to parse the Zabbix API URL from the config file.
    def _parse_url_from_conf(self):
        config = get_yaml()
        conf_url = config['api_url']
        logger.debug('Got the URL from the api conf: %s. To be verified.' % conf_url)
        if conf_url is None:
            return None
        else:
            if self._verify_url(conf_url) is False:
                return None
            else:
                return conf_url

    # Try to get the Zabbix API URL from user input.
    def _input_url(self):
        # Define local variables.
        tries = 0
        key_in_url = ''
        # Allow the user to input the URL of Zabbix API for 3 times and verify.
        while tries < 3 and self._verify_url(key_in_url) is False:
            tries += 1
            logger.debug('User to input the url for the %d time' % tries)
            key_in_url = input('Please provide the URL of your Zabbix API: ')
            logger.debug('User input URL = %s' % key_in_url)
        # Exceeded the 3-time limit but no valid URL input.
        if tries >= 3:
            logger.critical('No valid URL was input for 3 times. Raise an exception.')
            raise Exception('No valid URL was got from config file or user input for 3 times.')
        else:
            return key_in_url

    def get_url(self):
        # Firstly, try to get the URL from the config file.
        url = self._parse_url_from_conf()
        # If URL is not present in the conf, ask the user to input the URL.
        if url is None:
            logger.info('Did not get a valid URL from the config file. Turn to advise the user to input.')
            url = self._input_url()
        return url


#######################################
#    Section 4 - Zabbix Credential    #
#######################################
# Define a class ZabbixCredential to get the username and password of Zabbix API.
class ZabbixCredential:
    # Try to parse the credential from the config file.
    @staticmethod
    def _parse_cred_from_conf():
        config = get_yaml()
        username = config['user']['username']
        logger.debug('Obtaining the username %s from config file. To be verified.' % username)
        password = config['user']['password']
        logger.debug('Obtaining the password from config file. To be verified.')
        return username, password

    # Try to get the credential from user input.
    @staticmethod
    def _user_input_cred():
        # Define local variables.
        tries = 0
        key_in_username = key_in_password = ''
        # Allow the user to input credential for 3 times.
        while (tries < 3) and (key_in_password.strip() == '' or key_in_username.strip() == ''):
            tries += 1
            logger.debug('User to input the credential for the %d time' % tries)
            key_in_username = input('Username: ')
            logger.debug('User input username = %s' % key_in_username)
            key_in_password = input('Password: ')
            logger.debug('User input password = %s' % key_in_password)
        # Exceeded the 3-time limit but no valid credential input. Raise an exception.
        if tries >= 3:
            logger.critical('No valid credential was input for 3 times. Raise an exception.')
            raise Exception('No valid credential was got from config file or user input for 3 times.')
        # Got a valid credential from user input. Go ahead.
        logger.info('The credential is got from user input. Going ahead.')
        return key_in_username, key_in_password

    def get_cred(self):
        # Firstly, try to get the credential from config file.
        (username, password) = self._parse_cred_from_conf()
        # If no credential defined in the config file, ask the user to input the credential.
        if username is None or password is None:
            logger.info('Did not get a credential from config file. Turn to advise the user to input.')
            (username, password) = self._user_input_cred()
        return username, password


#######################################
#  Section 5 - Connection with Zabbix #
#######################################
# Define a class APIQuery to handle HTTP connections with Zabbix.
class ConnectionWithZabbix:
    def __init__(self, url, json_payload):
        # url, the URL of Zabbix API
        self.url = url
        # payload of HTTP request.
        self.json_payload = json_payload

    # Separate the URL to is_https, host, port and path.
    def _separate_url(self):
        if self.url.find('https') == -1:
            is_https = False
            host = self.url.replace('http://', '').partition(':')[0].partition('/')[0]
            port = self.url.replace('http://' + host, '').replace(':', '').partition('/')[0]
            path = self.url.replace('http://' + host, '').replace(':', '').replace(port, '')
        else:
            is_https = True
            host = self.url.replace('https://', '').partition(':')[0].partition('/')[0]
            port = self.url.replace('https://' + host, '').replace(':', '').partition('/')[0]
            path = self.url.replace('https://' + host, '').replace(':', '').replace(port, '')
        logger.info('The URL is separated to is_https, host, port and path.')
        return is_https, host, port, path

    # Get the configuration of HTTP query.
    def _get_http_config(self):
        (is_https, host, port, path) = self._separate_url()
        http_method = 'GET'
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Python/zabbix-api',
            'Cache-Control': 'no-cache'
        }
        return is_https, host, port, path, http_method, headers

    # Build SSL context, if the connection is HTTPS.
    @staticmethod
    def _build_ssl_context():
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        ssl_context.load_default_certs()
        logger.debug('Configured the SSL Context to load OS default trusted root store.')
        return ssl_context

    # Initiate the HTTP(S) connection.
    def _build_http_connection(self, is_https, host, port, path, http_method, headers, ssl_context):
        # Check if port has a value.
        if port == '':
            port = None
        # Check whether this is a HTTP or HTTPS connection.
        if is_https:
            conn = http.client.HTTPSConnection(host, port=port, context=ssl_context)
        else:
            conn = http.client.HTTPConnection(host, port=port)
        # Initiate the connection.
        try:
            conn.request(http_method, path, self.json_payload, headers)
            logger.info('Sent query to host %s, port %s, path, %s, Method %s, Headers %s, Payload %s'
                        % (host, port, path, http_method, headers, self.json_payload))
        # Handle HTTP connection timeout error. Put it in the log.
        except TimeoutError:
            logger.critical('HTTP connection to host %s, port %s, path %s has been time-out.'
                            % (host, port, path))
        # Handle other unknown errors. Put it in the log.
        except Exception as unknown_error:
            logger.critical(
                'HTTP connection to host %s, port %s, path %s has failed. Error: %s.'
                % (host, port, path, unknown_error))
        return conn

    # Parse the HTTP response.
    @staticmethod
    def _parse_http_response(conn, host, port, path):
        response = conn.getresponse()
        logger.info('Received the response from host %s, port %s, path %s.' % (host, port, path))
        # Verify if the status code of HTTP response is 200. If not, this is a bad response. Put it in the log.
        if response.getcode() != 200:
            logger.critical('HTTP response status code is %d. Raise an exception.' % response.getcode())
            raise Exception('HTTP error in the response from host %s, port %s, path %s, status code: %s'
                            % (host, port, path, response.getcode()))
        # The HTTP status code is fine. Parse the JSON content to a Python object.
        else:
            data = json.loads(response.read())
            logger.debug('content received from host %s, port %s, path %s: %s' % (host, port, path, data))
            return data

    # The main method to line up the methods above.
    def connect_zabbix(self):
        (is_https, host, port, path, http_method, headers) = self._get_http_config()
        conn = self._build_http_connection(is_https, host, port, path, http_method, headers, self._build_ssl_context())
        data = self._parse_http_response(conn, host, port, path)
        return data


#####################################
#  Section 6 - Meta Class of Query  #
#####################################
# Define a class MetaClassForQuery to form an API query to Zabbix.
class MetaClassForQuery:
    def __init__(self, url, token, params):
        # url, the URL of Zabbix API
        self.url = url
        # token is gotten from login function in another module.
        self.token = token
        # method to call Zabbix APIs.
        self.method = ''
        # parameters in the query payload. Can be retrieved by parsing configuration, or passed from an instance.
        self.params = params

    # Form the basic structure of query payload.
    def _generate_payload(self):
        logger.debug('Creating the base payload dict.')
        python_payload = {
            'jsonrpc': '2.0',
            'method': self.method,
            'params': self.params,
            'auth': self.token,
            'id': random.randint(0, 1000)
        }
        # Transfer from a python object to a JSON object.
        json_payload = json.dumps(python_payload)
        logger.info('JSON payload generated, content: %s' % json_payload)
        return json_payload

    def _verify_params(self):
        # Keep the method to allow child classes to override this method.
        pass

    # Basic verification. If the HTTP response content doesn't include 'result', this is a bad response..
    @staticmethod
    def _verify_result_basic(response):
        # A bad response does not contain 'result'.
        if 'result' not in response:
            if 'error' in response:
                logger.critical('Got an error from Zabbix. Code: %s, message: %s, data: %s'
                                % (response['error']['code'],
                                   response['error']['message'],
                                   response['error']['data']))
                raise Exception('Got an error from Zabbix. Please refer to logs for details.')
            else:
                logger.critical('Got NO result from the response. Unknown issue. Content: %s' % response)
                raise Exception('Got NO result. Unknown issue. Please refer to logs for details.')
        # A good response with 'result'.
        else:
            logger.info('Got results from the API response.')

    def _verify_result_advanced(self, response):
        # Keep the method to allow child classes to override this method.
        pass

    def api_query(self):
        # Verify if query payload parameters are valid or not. If not, it may stop processing.
        self._verify_params()

        # Send HTTP request to Zabbix and get the HTTP response.
        request = ConnectionWithZabbix(self.url, self._generate_payload())
        response = request.connect_zabbix()

        # Basic verification with the response.
        self._verify_result_basic(response)
        # Advanced verification with result may take place with child classes.
        self._verify_result_advanced(response)

        return response['result']


#####################################
#       Logging Configuration       #
#####################################
logger = configure_logger()
