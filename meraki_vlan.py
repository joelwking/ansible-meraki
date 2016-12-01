#!/usr/bin/python
#
"""

     Copyright (c) 2016 World Wide Technology, Inc.
     All rights reserved.


     Revision history:

     11 August 2016  |  1.0 - initial release

"""
DOCUMENTATION = '''

---

module: meraki_vlan
author: Joel W. King, World Wide Technology
version_added: "1.0"
short_description: Demonstration for Network Solutions VT

description:
    - Demonstration for Network Solutions VT 

options:

'''

EXAMPLES = '''

'''

# http://blog.toast38coza.me/custom-ansible-module-hello-world/
def main():
    module = AnsibleModule(
        argument_spec=dict(
            dashboard=dict(required=True),
            organization=dict(required=True)
            api_key=dict(required=True),
            network=dict(required=True),
            action=dict(required=False, default="add", choices=["add", "delete", "update"]),
            network=dict(required=True),
            vlan=dict(required=True),
            applianceIp=dict(required=True),
            subnet=dict(required=True)
        )
    )


    import Meraki_Connector as mc
    session = mc.Connector(API_key=module.param["api_key"])

    # Get Organization ID 
    orgs = session.get_org_ids()
    org_id = session.get_org_id(orgs, module.param["organization"])
    if not org_id:
        module.fail_json(msg="Organization %s, not found." %  module.param["organization"])

    # Get Network ID
    networks = session.get_networks(org_id)
    network_id = session.get_network_id(networks, module.param["network"])
    if not network_id:
        module.fail_json(msg="Network %s, not found." %  module.param["network"])

    # Add Logic, NOTE: create case structure and move to separate function when delete and update implemented
    if module.param["action"] == "add":
        body = {'applianceIp': None, 'id': None, 'name': None, 'subnet': None}
        for key in body.keys():
            body[key] = module.param[key]
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