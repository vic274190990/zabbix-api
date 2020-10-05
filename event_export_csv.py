# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 23:27
# @Author  : Gao, Jiezhang (Vic)
# @File    : event_export_csv.py

import time
import timeit
import datetime
import csv
import re

from modules import base_lib
from modules import apiinfo
from modules import user
from modules import problem
from modules import event
from modules import trigger


#####################################
#        Constant Definition        #
#####################################
SEVERITY_MAPPING = {
    '0': '0-Not_Classified',
    '1': '1-Information',
    '2': '2-Warning',
    '3': '3-Average',
    '4': '4-High',
    '5': '5-Disaster'
}

ACKNOWLEDGED_MAPPING = {
    '0': 'No',
    '1': 'Yes'
}

HEADERS = ['eventid', 'r_eventid', 'severity', 'name', 'type', 'time', 'recovery_time', 'duration', 'duration_readable',
           'acknowledged', 'hosts', 'groups']


#####################################
#         Funcs Query Input         #
#####################################
# Ask user if wishes to enquire "Recent" or "History" events.
def input_event_query_type():
    event_query_type = input('Do you wish to enquire "Recent" or "History" events? [History]')
    while not (event_query_type == 'History' or event_query_type == 'Recent' or event_query_type == ''):
        logger.error('Input %s is invalid.' % event_query_type)
        input('Your input %s is invalid.'
              'Do you wish to enquire "Recent" or "History" events? [History]' % event_query_type)
    if event_query_type == 'History' or event_query_type == '':
        logger.info('User opts to view historical events.')
        return 'History'
    else:
        logger.info('User opts to view recent events.')
        return 'Recent'


# Request user to input from_time and till_time time for event searching.
def input_event_timeframe():
    # Input from_time
    from_time = input('From when do you want to get the events? Example of format: 2020-05-03 18:59:36:')
    logger.debug('User input from_time: %s' % from_time)
    # Verify format and check if it is later than now.
    while base_lib.verify_time(from_time) is False \
            or base_lib.compare_time(time.localtime(time.time()),
                                     time.strptime(from_time, '%Y-%m-%d %H:%M:%S')) is False:
        logger.error('The from_time %s input is invalid or later than now. Request user to re-input.' % from_time)
        from_time = input('Invalid time input or later than now. Please provide the correct time.'
                          'From what time do you want to get the events? Example of format: 2020-05-03 18:59:36:')
    logger.info('The from_time %s input is valid.' % from_time)

    # Input till_time
    till_time = input('Till when do you want to get the events? Example of format: 2020-06-03 21:59:36 or Now:')
    logger.debug('User input till_time %s' % till_time)
    # Verify format and check if it is later than now.
    while (base_lib.verify_time(till_time) is False
           or base_lib.compare_time(time.localtime(time.time()),
                                    time.strptime(till_time, '%Y-%m-%d %H:%M:%S')) is False) \
            and till_time != 'Now':
        logger.error('The from_time %s input is invalid or later than now. Request user to re-input.' % till_time)
        till_time = input('Invalid time input or later than now. Please provide the correct time.'
                          'Till when do you want to get the events? Example of format: 2020-06-03 21:59:36 or Now:')
        logger.info('The till_time %s input is valid.' % till_time)

    # If till_time is Now, put in the current time.
    if till_time == 'Now':
        till_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.info('User input till_time is Now. Current time is %s' % till_time)

    # Cover to Unix timestamps
    from_time_stamp = time.mktime(time.strptime(from_time, '%Y-%m-%d %H:%M:%S'))
    logger.debug('Converted from_time to a Unix timestamp: %s' % from_time_stamp)
    till_time_stamp = time.mktime(time.strptime(till_time, '%Y-%m-%d %H:%M:%S'))
    logger.debug('Converted till_time to a Unix timestamp: %s' % till_time_stamp)
    return from_time_stamp, till_time_stamp


#####################################
#        Class Event's Time         #
#####################################
# Define a class to process the time, recover_time, duration of events.
class EventsTime:
    def __init__(self, pre_process_event, api_url, api_token):
        self.event = pre_process_event
        self.api_url = api_url
        self.api_token = api_token

    # A method to process the time for recent events - got from problem.get.
    def _process_recent_event_time(self):
        logger.debug('Start to process time for the event.')
        if not self.event['r_clock'] == '0':
            logger.debug('The event does have a recovery time.')
            self.event['duration'] = base_lib.calculate_time_delta(self.event['clock'], self.event['r_clock'])
            logger.debug('Calculated event duration in secs: %s' % self.event['duration'])
            self.event['duration_readable'] = base_lib.convert_to_readable_time(
                base_lib.calculate_time_delta(self.event['clock'], self.event['r_clock']))
            logger.debug('Calculated event duration in readable format: %s' % self.event['duration_readable'])
            self.event['time'] = datetime.datetime.fromtimestamp(int(self.event['clock']))
            logger.debug('Calculated event time: %s' % self.event['time'])
            self.event['recovery_time'] = datetime.datetime.fromtimestamp(int(self.event['r_clock']))
            logger.debug('Calculated event recovery time: %s' % self.event['recovery_time'])
        else:
            logger.debug('The event does NOT have a recovery time.')
            self.event['duration'] = None
            self.event['duration_readable'] = None
            self.event['time'] = datetime.datetime.fromtimestamp(int(self.event['clock']))
            logger.debug('Calculated event time: %s' % self.event['time'])
            self.event['recovery_time'] = None
        return self.event

    # A method to process the time for historical events - got from event.get.
    def _process_history_event_time(self):
        logger.debug('Start to process time for the event.')
        if not self.event['r_eventid'] == '0':
            # Prepare for the parameters to call event.get API.
            r_event_params = {
                'eventids': [self.event['r_eventid']],
                'output': [
                    'eventids',
                    'clock'
                ]
            }
            # Call event.get API to get the information of recovery event associated to the event.
            inst_r_events = event.EventGet(self.api_url, self.api_token, r_event_params)
            r_events = inst_r_events.api_query()
            # Get the clock of recovery event, to put in 'r_clock' of the targeted event.
            self.event['r_clock'] = r_events[0]['clock']
            logger.debug('The r_clock for the event is %s' % self.event['r_clock'])
            # Process the rest time attributes.
            self.event['duration'] = base_lib.calculate_time_delta(self.event['clock'], self.event['r_clock'])
            logger.debug('Calculated event duration in secs: %s' % self.event['duration'])
            self.event['duration_readable'] = base_lib.convert_to_readable_time(
                base_lib.calculate_time_delta(self.event['clock'], self.event['r_clock']))
            logger.debug('Calculated event duration in readable format: %s' % self.event['duration_readable'])
            self.event['time'] = datetime.datetime.fromtimestamp(int(self.event['clock']))
            logger.debug('Calculated event time: %s' % self.event['time'])
            self.event['recovery_time'] = datetime.datetime.fromtimestamp(int(self.event['r_clock']))
            logger.debug('Calculated event recovery time: %s' % self.event['recovery_time'])
        else:
            self.event['duration'] = None
            self.event['duration_readable'] = None
            self.event['time'] = datetime.datetime.fromtimestamp(int(self.event['clock']))
            logger.debug('Calculated event time: %s' % self.event['time'])
            self.event['recovery_time'] = None
        return self.event

    # Process the time, recover_time, duration of events.
    def process(self):
        if 'r_clock' in self.event:
            # This is a recent event - problem, process recent event time.
            self._process_recent_event_time()
        elif 'r_eventid' in self.event:
            # This is a history event - event, process history event time.
            self._process_history_event_time()
        else:
            raise Exception('Zabbix API error. Neither r_clock nor r_eventid was define in API response.')
        return self.event


#####################################
#       Class Event's Trigger       #
#####################################
# Define a class to describe the trigger information linked to the event by calling API trigger.get
class EventsTrigger:
    def __init__(self, triggerid, api_url, api_token):
        self.triggerid = triggerid
        self.api_url = api_url
        self.api_token = api_token

    def get(self):
        # Prepare for the parameters to call trigger.get API.
        trigger_params = {
            'triggerids': self.triggerid,
            'output': [
                'triggerid',
                'description',
                'templateid',
                'priority'
            ],
            'selectHosts': [
                'hostids',
                'name'
            ],
            'selectGroups': [
                'groupid',
                'name'
            ],
            'selectTags': 'extend'
        }
        # Call trigger.get API to get the information of triggers associated to the event.
        inst_triggers = trigger.TriggerGet(self.api_url, self.api_token, trigger_params)
        triggers = inst_triggers.api_query()
        return triggers[0]


#####################################
#      Class Event's Severity       #
#####################################
# Define a class to get the severities of events.
class EventsSeverity:
    def __init__(self, api_version, pre_process_event, linked_trigger):
        self.api_version = api_version
        self.event = pre_process_event
        self.trigger = linked_trigger

    def get(self):
        # For Zabbix v4 or v5, there is severity attribute for event. Just do mapping.
        if re.search(r'^(5\.|4\.)', self.api_version, re.I) is not None:
            logger.debug('This is Zabbix v4 or above, directly map the severity.')
            self.event['severity'] = SEVERITY_MAPPING[self.event['severity']]
            logger.debug('Mapped the severity of this event: %s' % self.event['severity'])
            return self.event
        # For Zabbix v3 or below, turn to call trigger.get to get severity information.
        if self.event['source'] == '0' and self.event['object'] == '0' and not self.event['objectid'] == '0':
            logger.debug('This is Zabbix v3 or below, call trigger.get to get the severity.')
            self.event['severity'] = SEVERITY_MAPPING[self.trigger['priority']]
            logger.debug('Mapped the severity of this event: %s' % self.event['severity'])
            return self.event


#####################################
#         Class Event's Name        #
#####################################
# Define a class to get the name of events associated to triggers, applicable only for Zabbix v3 or below.
class EventsName:
    def __init__(self, pre_process_event, linked_trigger):
        self.event = pre_process_event
        self.trigger = linked_trigger

    def get(self):
        self.event['name'] = self.trigger['description']
        logger.debug('Mapped the name of this event: %s' % self.event['name'])
        return self.event


#####################################
#  Class Event's Hosts And Groups   #
#####################################
# Define a class to get the information of triggers which created respective events.
class EventsHostsAndGroups:
    def __init__(self, pre_process_event, linked_trigger):
        self.event = pre_process_event
        self.trigger = linked_trigger

    # Pick up names for "triggers" object and put them to a string.
    def _process_names_list2string(self, obj_trigger):
        # Create a temporary list to pick up names of 'obj_trigger' in the 'triggers'.
        temp_objs = []
        for host in range(len(self.trigger[obj_trigger])):
            temp_objs.append(self.trigger[obj_trigger][host]['name'])
        # Form 'temp_hosts' list to a string.
        return ' ,'.join(temp_objs)

    # Get the information of triggers which created respective events. And add more information to the events.
    def get(self):
        # Ensure that the event was created by a trigger.
        if self.event['source'] == '0'\
                and self.event['object'] == '0'\
                and not self.event['objectid'] == '0':
            # Add hosts info to the event
            self.event['hosts'] = self._process_names_list2string('hosts')
            # Add groups info to the event
            self.event['groups'] = self._process_names_list2string('groups')
        return self.event


#####################################
#        Class Event's Type         #
#####################################
# Define a class to describe 'type' of event, retrieve from the tag 'type', and put its value to the attribute 'type'.
class EventsType:
    def __init__(self, pre_process_event):
        self.event = pre_process_event

    def get(self):
        self.event['type'] = ''
        for tag in self.event['tags']:
            for tag_attr in tag:
                if tag[tag_attr] == 'type':
                    self.event['type'] = tag['value']
                    break
            else:
                continue
            break


#####################################
#       Class Event To Export       #
#####################################
# Define a class to describe every event to be processed.
class EventToExport:
    def __init__(self, api_version, pre_process_event, api_url, api_token):
        self.api_version = api_version
        self.event = pre_process_event
        self.api_url = api_url
        self.api_token = api_token

    def process(self):
        # Process the time, recover_time, duration of events.
        inst_events_time = EventsTime(self.event, self.api_url, self.api_token)
        inst_events_time.process()

        # Get the information of triggers linked to events, by calling API trigger.get.
        inst_triggers = EventsTrigger(self.event['objectid'], self.api_url, self.api_token)
        the_trigger = inst_triggers.get()

        # Get the information of severity of the event.
        inst_severity = EventsSeverity(self.api_version, self.event, the_trigger)
        inst_severity.get()

        # Get the name of events, applicable ONLY for Zabbix v3 or below)
        if re.search(r'^(5\.|4\.)', self.api_version, re.I) is not None:
            logger.info('This is Zabbix v4 or above, no need to do anything.')
        else:
            logger.info('This is Zabbix v3 or below, call trigger.get to get the name of events.')
            inst_name = EventsName(self.event, the_trigger)
            inst_name.get()

        # Get the information of hosts and groups of the event.
        inst_events_hosts_and_groups = EventsHostsAndGroups(self.event, the_trigger)
        inst_events_hosts_and_groups.get()

        # find the 'type' tag in the event, and clean up other tags.
        inst_events_type = EventsType(self.event)
        inst_events_type.get()

        # Acknowledged mapping
        logger.info('Start to process acknowledgement.')
        if re.search(r'^(5\.|4\.)', self.api_version, re.I) is not None:
            self.event['acknowledged'] = ACKNOWLEDGED_MAPPING[self.event['acknowledged']]
            logger.info('This is Zabbix v4 or above, Acknowledgement can be mapped')
        else:
            if 'acknowledged' in self.event:
                self.event['acknowledged'] = ACKNOWLEDGED_MAPPING[self.event['acknowledged']]
                logger.info('This is Zabbix v3 or below, historical event acknowledgement can be mapped.')
            else:
                self.event['acknowledged'] = None
                logger.info('This is Zabbix v3 or below, recent event acknowledgement is unavailable.')

        # Delete attributes not needed.
        for attribute in list(self.event):
            if attribute not in HEADERS:
                del self.event[attribute]
        return self.event


#####################################
#             Main Body             #
#####################################
logger = base_lib.configure_logger()

if __name__ == "__main__":
    # Get output CSV filename - interactive.
    inst_csv_filename = base_lib.CsvFilename()
    csv_filename = inst_csv_filename.user_input()

    # Get if historical or recent events and timeframe  - interactive.
    history_or_recent = input_event_query_type()
    if history_or_recent == 'History':
        (time_from, time_till) = input_event_timeframe()
    else:
        time_from = time_till = None

    # Get URL - may be interactive.
    inst_url = base_lib.ZabbixURL()
    url = inst_url.get_url()

    # Get the token after login - may be interactive.
    inst_login = user.UserLogin(url)
    token = inst_login.api_query()

    # Running timer starts ticking.
    program_start_time = timeit.default_timer()

    # Get Zabbix API verizon
    inst_zbx_api_version = apiinfo.ApiinfoVersion(url)
    zbx_api_version = str(inst_zbx_api_version.api_query())

    # For historical event - event.get query:
    if history_or_recent == 'History':
        # Initiate the event.get query, get event from Zabbix
        event_params = {
            'output': 'extend',
            'time_from': time_from,
            'time_till': time_till,
            'value': [1, 2, 3],
            'selectAcknowledges': 'extend',
            'selectTags': 'extend',
            'sortfield': ['clock'],
            'sortorder': 'ASC'
        }
        inst_events = event.EventGet(url, token, event_params)
        zbx_events = inst_events.api_query()
    # For recent event query - problem.get query:
    else:
        # Initiate the problem.get query, get event from Zabbix
        problem_params = {
            'output': 'extend',
            'recent': True,
            'selectAcknowledges': 'extend',
            'selectTags': 'extend',
            'sortfield': ['eventid'],
            'sortorder': 'ASC'
        }
        inst_problems = problem.ProblemGet(url, token, problem_params)
        zbx_events = inst_problems.api_query()

    # Processing the list 'events'.
    for zbx_event in zbx_events:
        inst_event_to_export = EventToExport(zbx_api_version, zbx_event, url, token)
        inst_event_to_export.process()

    # Finished the work with Zabbix API. Logout.
    logout = user.UserLogout(url, token)
    logout.api_query()

    # Create CSV, and put in the data.
    logger.info('Creating a CSV file %s' % csv_filename)
    with open(csv_filename, 'w', newline='') as f:
        f_csv = csv.DictWriter(f, HEADERS)
        f_csv.writeheader()
        logger.debug('Wrote the headers.')
        f_csv.writerows(zbx_events)
        logger.debug('Wrote the content.')

    # Running timer stops ticking.
    program_end_time = timeit.default_timer()
    logger.info('Program running time is %s' % (program_end_time - program_start_time))
