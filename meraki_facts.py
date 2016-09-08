#!/usr/bin/env python

"""
     Copyright (c) 2015 World Wide Technology, Inc.
     All rights reserved.

     Revision history:
     7 September 2016  |  1.0 - initial release


"""

DOCUMENTATION = '''
---
module: meraki_facts.py
author: Joel W. King, World Wide Technology
version_added: "1.0"
short_description: Locate devices in a Meraki Cloud Managed Network and return as facts
description:
    - Gather facts about clients for the organization, network, and devices in a Meraki network.
 
requirements:
    - Meraki_connector.py

options:
    dashboard:
        description:
            - hostname of the dashboard, default is dashboard.meraki.com
        required: False
    apikey:
        description:
            - API key, for authentication and association with an organization.
        required: True
    timespan:
        description:
            - The timespan for which clients will be fetched. Must be at most one month and in seconds.
        required: False
    search_string:
        description:
            - Search for this string in client description and MAC, return all clients if not specified
        required: False
    
'''

EXAMPLES = '''

  Sample inventory file and execution from shell

  [meraki_dashboard]
  dashboard.meraki.com ansible_connection=local ansible_ssh_user=administrator

  ansible -m meraki_facts meraki_dashboard -a 'apikey=f62bc7d1d'

  Sample playbook

  - name: gather facts about the cloud
    meraki_facts:
      dashboard: "{{dashboard}}"
      apikey: "{{meraki_params.apikey}}"
      timespan: 1200
      search_string: "WIZ"

'''


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    "Locate devices in a Meraki Cloud Managed Network and return as facts"

    module = AnsibleModule(argument_spec = dict(
             apikey = dict(required=True),
             dashboard = dict(required=False),
             search_string = dict(required=False),
             timespan = dict(required=False)
             ),
             check_invalid_arguments=False,
             add_file_common_args=True)

    # Import the Class

    try:
        import Meraki_Connector
    except ImportError:
        sys.path.append("/usr/share/ansible")
    try:
        import Meraki_Connector
        HAS_LIB=True
    except:
        HAS_LIB=False
        module.fail_json(msg="Import error of Meraki_Connector")
    
    # Handle arguments (value is None if optional arguemtn not specified)

    apikey = module.params["apikey"]
    dashboard = module.params["dashboard"]
    search_string = module.params["search_string"]
    timespan = module.params["timespan"]

    if dashboard:
        meraki = Meraki_Connector.Connector(API_key=apikey, dashboard=dashboard)
    else:
        meraki = Meraki_Connector.Connector(API_key=apikey)

    if timespan:
        meraki.set_parameters(timespan=timespan)
    if search_string:
        meraki.set_parameters(search_string=search_string)

    # Gather facts from the cloud

    if meraki.locate_device():
        module.exit_json(**meraki.result)
    else:
        module.fail_json(msg="%s %s" % (meraki.app_run_status, meraki.progress))

from ansible.module_utils.basic import *
main()
#
