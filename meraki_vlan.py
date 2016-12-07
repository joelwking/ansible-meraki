#!/usr/bin/python
#
"""

     Copyright (c) 2016 World Wide Technology, Inc.
     All rights reserved.

     Revision history:

     7 December 2016  |  1.0 - initial release

"""
DOCUMENTATION = '''
---

module: meraki_vlan
author: Joel W. King, World Wide Technology
version_added: "1.0"
short_description: Manage VLANs on Meraki Networks

description:
    - Manage VLANs on Meraki Networks

requirements:
    -  ansible-meraki/Meraki_Connector.py from https://github.com/joelwking
options:
    dashboard:
        description:
            - Meraki dashboard host name, e.g. dashboard.meraki.com
        required: true

    organization:
        description:
            - organization name
        required: true  

    api_key:
        description:
            - the API key for the organization administrator under My Profile
        required: true      

    action:
        description:
            - desired action, add, delete, update, default is add
        required: false 

    network:
        description:
            - Name of the network
        required: true       

    id:
        description:
            - VLAN number
        required: true     

    name:
        description:
            - VLAN name
        required: true     

    applianceIp:
        description:
            - The default gateway IP address, 192.0.2.1
        required: true     

    subnet:
        description:
            - Layer 3 network address of the VLAN, with mask 192.0.2.0/24
        required: true     

'''

EXAMPLES = '''

  - name: manage vlans
    meraki_vlan:
      dashboard: "{{inventory_hostname}}"
      organization: "{{meraki.organization}}"
      api_key: "{{meraki_params.apikey}}"
      action: add                            # add, delete update
      network: "{{meraki.network}}"          # Name of the network
      id: "1492"                             # VLAN number
      name: VLAN1492                         # VLAN name
      applianceIp: "192.0.2.1"               # Default Gateway IP address
      subnet: "192.0.2.0/24"                 # Layer 3 network address of the VLAN

'''

def main():
    "# http://blog.toast38coza.me/custom-ansible-module-hello-world/"
    module = AnsibleModule(
        argument_spec=dict(
            dashboard=dict(required=True),
            organization=dict(required=True),
            api_key=dict(required=True),
            action=dict(required=False, default="add", choices=["add", "delete", "update"]),
            network=dict(required=True),
            name=dict(required=True),
            id=dict(required=True),
            applianceIp=dict(required=True),
            subnet=dict(required=True)
        )
    )


    try:
        import Meraki_Connector as mc
    except ImportError:
        module.fail_json(msg="Meraki_Connector required for this module")

    session = mc.Connector(API_key=module.params["api_key"])

    # Get Organization ID 
    orgs = session.get_org_ids()
    org_id = session.get_org_id(orgs, module.params["organization"])
    if not org_id:
        module.fail_json(msg="Organization %s, not found." %  module.params["organization"])

    # Get Network ID
    networks = session.get_networks(org_id)
    network_id = session.get_network_id(networks, module.params["network"])
    if not network_id:
        module.fail_json(msg="Network %s, not found." %  module.params["network"])

    # Add Logic, NOTE: create case structure and move to separate function when delete and update implemented
    if module.params["action"] == "add":
        body = {'applianceIp': None, 'id': None, 'name': None, 'subnet': None}
        for key in body.keys():
            body[key] = module.params[key]
        result = session.POST("/api/v0/networks/" + network_id + "/vlans", body)
    else:
        module.fail_json(msg="Delete and Update not implemented")

    # Wrap up
    status_code = session.get_last_status_code()
    if status_code in mc.Connector.successful_POST_status:
       module.exit_json(changed=True, status_code=status_code, result=result)
    else:
       module.fail_json(msg="%s %s" % (status_code, result))


from ansible.module_utils.basic import *
main()
#