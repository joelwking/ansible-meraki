#
"""
     Copyright (c) 2016 World Wide Technology, Inc.
     All rights reserved.

     Revision history:
     6 September 2016  |  1.0 Initial release. 
     30 November 2016  |  1.1 added additional methods for Programming Meraki APIs VT call

     module: Connector.py
     author: Joel W. King, World Wide Technology
     short_description: Class to manage the connection to Meraki Cloud

"""
#
#  system imports
#
import json
import time
import requests
import httplib

# ========================================================
# Meraki_Connector
# ========================================================

class Connector(object):
    " Class variables, shared by all instances of the class "
    BANNER = "MERAKI"
    APP_ERROR = 0
    APP_SUCCESS = 1
    successful_POST_status =  (201,)


    def __init__(self, API_key=None, dashboard="dashboard.meraki.com"):
        """
        Instance variables, belongs only to the current instance of a class.
        """
        self.HEADER = {"Content-Type": "application/json"}
        self.status_codes = []                             # List of all status codes   
        self.progress = []                 
        self.app_run_status = Connector.APP_SUCCESS
        self.result = { 'ansible_facts': {'meraki': [] }}

        # Configuration variables

        self.configuration = dict()
        self.configuration["Meraki-API-Key"] = API_key
        self.configuration["dashboard"] = dashboard

        # Parameters

        self.param = dict()
        self.param["search_string"] = "*"                  # Return all devices              
        self.param["timespan"] = 2592000                   # The Whole Enchilada, one month of data

        try:
            requests.packages.urllib3.disable_warnings()
        except AttributeError:
            # Older versions of Requests do not support 'disable_warnings'
            pass
        

    def debug_print(self, message):
        "NOT IMPLEMENTED: Method, a function that is defined in a class definition."
        return None

    def set_status_save_progress(self, status, message):
        "Set status and append to the progress message, for debugging"
        self.app_run_status = status
        self.progress.append(message)
        return

    def get_configuration(self, requested_key):
        "Return requested key or None if the key does not exist."
        try:
            return self.configuration[requested_key]
        except:
            return None

    def get_data_size(self):
        "Return the number of elements in our list of clients"
        return len(self.result['ansible_facts']['meraki'])

    def add_data(self, response):
        "Each client dictionary is a list element"
        self.result['ansible_facts']['meraki'].append(response)
        return None

    def set_status(self, status):
        self.app_run_status = status
        return None

    def get_status(self):
        "get the current status, return either APP_SUCCESS or APP_ERROR"
        return self.app_run_status

    def get_last_status_code(self):
        "return the most recent status code"
        return self.status_codes[-1]

    def get_network_id(self, list_of_networks, network_name):
        """
        A query to get_networks returns a list of configured networks.
        This routine returns the network 'id' for a given network 'name', or None
        """
        for network in list_of_networks:
            if network_name == network['name']:
                return network['id']
        return None

    def get_org_id(self, list_of_orgs, org_name):
        """
        A query to get_org_ids returns a list of the orgizations managed by this administrator
        This routine returns the org 'id' for a given org 'name', or None
        """
        for org in list_of_orgs:
            if org_name == org['name']:
                return org['id']
        return None

    def set_parameters(self, **kwargs):
        " If the parameters is an empty dictionary, use the default values."
        for key, value in kwargs.items():
           self.param[key] = value

        self.debug_print("%s SET_PARAMETERS parameters:\n%s" % (Connector.BANNER, self.param))
        return

    def locate_device(self):
        """
        Locating client devices means walking a tree based on the API Key. The key is associated with one or more organizations,
        an organization can have one or more networks, each network can have multiple devices, and each device can have one or
        more client machines. Depending on the timespan specified, you may see differing results. Larger timespans may show the same
        client connected to multiple devices. Small timespans, may not return any results.
        """

        org_id_list = self.get_org_ids()
        for organization in org_id_list:
            networks_list = self.get_networks(organization["id"])
            for network in networks_list:
                device_list = self.get_devices(network["id"])
                for device in device_list:
                    client_list = self.get_clients(device["serial"], self.param["timespan"])
                    for client in client_list:
                        response = self.build_output_record(self.param["search_string"], organization, network, device, client)
                        if response:
                            self.add_data(response)

        if self.get_data_size() > 0:
            self.set_status_save_progress(Connector.APP_SUCCESS, "Returned: %s clients" % self.get_data_size())
        else:
            self.set_status_save_progress(Connector.APP_ERROR, "Returned: %s clients" % self.get_data_size())

        self.debug_print("%s Data size: %s" % (Connector.BANNER, self.get_data_size()))
        return self.get_status()

    def build_output_record(self, search_string, organization, network, device, client):
        """
        Match the search string against the client MAC and description, if there is a match return a dictionary to add to
        the Action Result data field. A search string of "*" means to return everything.
        """
        self.debug_print("%s BUILD_OUTPUT_RECORD for: %s %s %s" % (Connector.BANNER, device["serial"], client['description'], client['mac']))

        if client['description'] is None:                  # Description could be NoneType
            client['description'] = ""

        if search_string == "*" or search_string in client['description'] or search_string in client['mac']:

            return {'client': {'ip': client['ip'], 'mac': client['mac'], 'description': client['description'], 'dhcpHostname': client['dhcpHostname']},
                    'device': device['name'], 
                    'network': network['name'], 
                    'organization': organization['name']}
        return None

    def get_org_ids(self):
        """
        Return a list of organization IDs for this account
        URI = "https://dashboard.meraki.com/api/v0/organizations"
        return [{"id":530205,"name":"WWT"}]
        """
        return self.query_api("/api/v0/organizations")

    def get_networks(self, organization_id):
        """
        Return a list of network IDs for this organization
        URI = "https://dashboard.meraki.com/api/v0/organizations/530205/networks"
        return [{u'id': u'L_629378047925028460', u'name': u'SWISSWOOD', u'organizationId': u'530205', u'tags': u'',
                 u'timeZone': u'America/New_York',  u'type': u'combined'}]
        """
        return self.query_api("/api/v0/organizations/" + str(organization_id) + "/networks")

    def get_devices(self, network_id):
        """
        Return a list of devices in this network
        URI = "https://dashboard.meraki.com/api/v0/networks/L_629378047925028460/devices"
        return [{u'address': u'swisswood dr, Denton, NC 16713', u'lat': 34.9543899, u'lng': -77.721312,
                 u'mac': u'88:15:44:08:ad:08',  u'model': u'MX64',  u'name': u'SWISSWOOD-MX64', u'serial': u'Q2KN-R9P3-3U6X',
                 u'tags': u' recently-added ', u'wan1Ip': u'192.168.0.3', u'wan2Ip': None}]
        """
        return self.query_api("/api/v0/networks/" + network_id + "/devices")

    def get_clients(self, serial, timespan):
        """
        Return a list of clients associated with this device serial number.
        URI = "https://dashboard.meraki.com/api/v0/devices/Q2HP-NAY7-A2WH/clients?timespan=86400"
        return [{u'description': u'alpha_b-THINK-7', u'dhcpHostname': u'alpha_b-THINK-7', u'id': u'k7c0271',
                 u'mac': u'60:6c:77:01:22:42',
                 u'mdnsName': None, u'switchport': u'3', u'usage': {u'recv': 14168.0, u'sent': 124917.00000000001}}]
        """
        if timespan > 2592000:
            timespan = 2592000
        timespan = str(timespan)
        return self.query_api("/api/v0/devices/" + serial + "/clients?timespan=" + timespan)

    def get_VLANS(self, network_id):
        """
        Return a list of VLANS for this network_id
        'https://dashboard.meraki.com/api/v0/networks/[networkId]/vlans'
        """
        return self.query_api("/api/v0/networks/" + network_id + "/vlans")

    def build_URI(self, URL):
        "Format the URL for the request and return"
        header = self.HEADER
        header["X-Cisco-Meraki-API-Key"] = self.get_configuration("Meraki-API-Key")
        return "https://" + self.get_configuration("dashboard") + URL

    def build_header(self):
        "Add the API key to the header and return"
        header = self.HEADER
        header["X-Cisco-Meraki-API-Key"] = self.get_configuration("Meraki-API-Key")
        return header

    def query_api(self, URL):
        """
        Method to query and return results, return an empty list if there are connection error(s).
        """
        try:
            r = requests.get(self.build_URI(URL), headers=self.build_header(), verify=False)
        except requests.ConnectionError as e:
            self.set_status_save_progress(Connector.APP_ERROR, str(e))
            return []
        self.status_codes.append(r.status_code)

        try:
            return r.json()
        except ValueError:                                 # If you get a 404 error, throws a ValueError exception
            return []

    def POST(self, URL, body):
        """
        Method to POST (Add) to the configuration. Return empty dictionary if there are connection errors.
        The body is a dictionary, which is converted to json.

        Sample return values are:
        {u'errors': [u'Validation failed: Vlan has already been taken']}
        {u'applianceIp': u'192.168.64.1', u'id': 64, u'name': u'VLAN64', u'networkId': u'L_6228460', u'subnet': u'192.168.64.0/24'}
        """
        try:
            r = requests.post(self.build_URI(URL), headers=self.build_header(), data=json.dumps(body), verify=False)
        except requests.ConnectionError as e:
            self.set_status_save_progress(Connector.APP_ERROR, str(e))
            return dict()
        self.status_codes.append(r.status_code)

        try:
            return r.json()
        except ValueError:
            return dict()