import requests, json, os
from dotenv import load_dotenv
from pprint import pprint
from requests.auth import HTTPBasicAuth

load_dotenv()

# API_CREDENTIALS
ZITIBASTIONS_CLIENT_ID=os.getenv('ZITIBASTIONS_CLIENT_ID')
ZITIBASTIONS_CLIENT_SECRET=os.getenv('ZITIBASTIONS_CLIENT_SECRET')
CUSTOMER_CLIENT_ID=os.getenv('CUSTOMER_CLIENT_ID')
CUSTOMER_CLIENT_SECRET=os.getenv('CUSTOMER_CLIENT_SECRET')
NETFOUNDRY_CUSTOMER_CLIENT_ID=os.getenv('NETFOUNDRY_CUSTOMER_CLIENT_ID')
NETFOUNDRY_CUSTOMER_CLIENT_SECRET=os.getenv('NETFOUNDRY_CUSTOMER_CLIENT_SECRET')
ZENDESK_API_USER=os.getenv('ZENDESK_API_USER')
ZENDESK_API_TOKEN=os.getenv('ZENDESK_API_TOKEN')
# NETWORK_OBJECT_IDS
CS_LAB_NETWORK_ID="0f4dd45d-8738-4e8e-b7a9-005d683ecb07"
ZITI_BASTION_NETWORKID = "d3b30838-1dcd-4268-9e7a-4821f58b783e"
ZITI_BASTIONS_PREFERRED_EDGEROUTER_NAME="bastion.production.netfoundry.io"
# ZITI_BASTIONS_PREFERRED_EDGEROUTER_ID="ea5eaac4-7fa1-4355-a611-b0744381d9cc" # ID
ZITI_BASTIONS_PREFERRED_EDGEROUTER_ID="7baa0801-b57a-4ca0-9c15-f68aad3c6178"
ZITI_BASTIONS_PREFERRED_EDGEROUTER_HOSTID="b21e5caf-5f91-4ec1-bced-1314bb3f5e1e"
NFORYZ_PREFERRED_EDGEROUTER_ID="6e6a77d5-7428-45ec-bd6f-87fa049ab31b"
CSLAB_PREFERRED_EDGEROUTER_ID="eff69be5-0730-4781-a335-2d101a7e396b"
# OBJECT_NAMES
APPWAN_NAME = os.environ.get('APPWAN_NAME')
APPWAN_ID=""
OPS_SERVER_ENDPOINT_NAME="ops.server.endpoint"
ENTITY_ATTRIBUTE="#support.temp.access.entity"
ENDPOINT_ATTRIBUTE_PREFIX="#ops.ssh.access.endpoint"
SERVICE_ATTRIBUTE_PREFIX="#ops.ssh.access.service"
# ZENDESK
NF_ZENDESK_BASE_URL='https://netfoundry.zendesk.com'
ZENDESK_FORM_NETWORK_FIELD_NAME="ziti_network_id"
ZENDESK_FORM_NETWORK_FIELD_ID="18522170008973"

incoming_json = {
  "authorization": "nf_secret_token",
  "ticket": {
      "id": 11245,
      "assignee": "chris.walker@netfoundry.io",
      "title": "Ticket Title",
      "description": "something is broken",
      "customer_name": "CUSTOMER1",
      "network_id": "15599fd6-881e-40ff-990a-34ba395749cb", # technilium-demo
      "priority": "high",
      "status": "open",
      "requester_name": "chris walker",
      "requester_email": "chris.walker@netfoundry.io",
      "ticket_priority": "high"
  }
}


def get_console_bearer_token(client_id, client_secret) -> str:
    url = 'https://netfoundry-production-xfjiye.auth.us-east-1.amazoncognito.com/oauth2/token'

    payload = 'grant_type=client_credentials&client_id={}'.format(client_id)
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    res = requests.post(url, headers=headers, data=payload, auth=(client_id, client_secret)).json()
    # print('\nResponse from get_token: {}'.format(json.dumps(res, indent=4)))

    access_token = res['access_token']
    # print('\naccess_token returned from get_console_bearer_token(): {}'.format(access_token))

    return access_token


def list_networks(bearer_token: str) -> []:
    url = 'https://gateway.production.netfoundry.io/core/v2/networks'
    headers={'Authorization': 'Bearer {}'.format(bearer_token), 'Content-Type': 'application/hal+json'}
    res = requests.get(url=url, headers=headers).json()

    network_list = res['_embedded']['networkList']
    # network_name = network_list['name']
    # network_id = network_list['id']
    # network_dict = {}
        
    # print('\nResponse from calling get networks: {}'.format(json.dumps(network_list, indent=4)))
    print('\nAll Network Tuples: ')
    print('============================')
    network_tuple_list = []
    for n in network_list:  
        # network_dict = {n['name'], n['id']}
        network_tuple = (n['name'], n['id'])        
        network_tuple_list.append(network_tuple)
        print('->: {}'.format(network_tuple)) 

    print('\nFinal network_tuple_list: {}'.format(network_tuple_list)) 

    return network_tuple_list


def get_network_host_urls(bearer_token: str, network_id: str) -> []:
    url = 'https://gateway.production.netfoundry.io/core/v2/networks/{}'.format(network_id)
    headers={'Authorization': 'Bearer {}'.format(bearer_token), 'Content-Type': 'application/hal+json'}
    res = requests.get(url=url, headers=headers).json()    

    # edge_policy_url = res['_links']['edge-router-policies']['href']
    network_host_url = res['_links']['hosts']['href']
    controller_url = res['_links']['network-controllers']['href']
    edge_router_url = res['_links']['edge-routers']['href']

    print('\nNetwork: {}'.format(json.dumps(res, indent=4)))

    return [network_host_url, controller_url, edge_router_url]


# def get_hosts_url(bearer_token: str, network_id: str) -> str:
#     url = 'https://gateway.production.netfoundry.io/core/v2/networks/{}'.format(network_id)
#     headers={'Authorization': 'Bearer {}'.format(bearer_token), 'Content-Type': 'application/hal+json'}
#     res = requests.get(url=url, headers=headers).json()

#     # print('\nResponse from get_hosts_url: {}'.format(json.dumps(res, indent=4)))

#     return res['_links']['hosts']['href']


def get_hosts(bearer_token: str, network_host_url: str):
    headers={'Authorization': 'Bearer {}'.format(bearer_token), 'Content-Type': 'application/hal+json'}
    res = requests.get(url=network_host_url, headers=headers).json()
    # print('\nHost data for network: \n{}'.format(json.dumps(res, indent=4)))

    host_list = res['_embedded']['hostList']

    # print('\nHost List returned from get_hosts: {}'.format(json.dumps(host_list, indent=4)))

    host_ip_list = []
    host_dict = {}

    for h in host_list:
        # print('\nHost: \n{}'.format(json.dumps(h, indent=4)))
        id = h['id']
        ip = h['ipAddress']

        if ip is not None:
            # host_ip_list.append(ip)
            host_dict[id] = ip

    # print('\nHOST_DICT: \n{}'.format(json.dumps(host_dict, indent=4)))
    return host_dict


####################
# ENTITY_FUNCTIONS #
####################
def create_entity(bearer_token: str, assignee: str, network_id: str):
    '''
    SUMMARY: Create temporary entity for support rep attached to ticket
    '''
    url = 'https://gateway.production.netfoundry.io/core/v2/services'
    headers={'Authorization': 'Bearer {}'.format(bearer_token), 'Content-Type': 'application/hal+json'}

    payload = {
        "selected": False,
        "attributes": [
            ENTITY_ATTRIBUTE
        ],
        "enrollmentMethod": {
            "ott": True
        },
        "networkId": network_id,
        "name": "support.temp.access.endpoint.{}".format(assignee)
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    print('Create Entity Response: \n{}'.format(json.dumps(response.json(), indent=4)))


def update_entity_attributes(bearer_token: str, entity_id: str, ticket_id: str, attributes: list):
    url = 'https://gateway.production.netfoundry.io/core/v2/endpoints/{}'.format(entity_id)
    headers={'Authorization': 'Bearer {}'.format(bearer_token), 'Content-Type': 'application/hal+json'}

    attributes.append("{}-{}".format(ENDPOINT_ATTRIBUTE_PREFIX, ticket_id))

    payload = {
        "attributes": attributes
    }

    print('\nUpdating entity attributes with payload: {}'.format(json.dumps(payload, indent=4)))
    res = requests.patch(url, headers=headers, data=json.dumps(payload)).json()
    print('\nResponse from updating entity attributes: {}'.format(json.dumps(res, indent=4)))
    # res.status_code

def update_entity(bearer_token: str, assignee_email: str, ticket_id: str, network_id: str, workflow: None|str):    
    # First, lookup the current entity:
    url = 'https://gateway.production.netfoundry.io/core/v2/endpoints?networkId={}&size=300&sort=name%2Casc'.format(network_id)
    headers={'Authorization': 'Bearer {}'.format(bearer_token), 'Content-Type': 'application/hal+json'}
    res = requests.get(url, headers=headers).json()
    endpoint_list = res['_embedded']['endpointList']
    # print('Response from lookup_rep_entity: \n{}'.format(json.dumps(endpoint_list, indent=4)))

    rep_id = assignee_email.split('@')[0]

    endpoint_id = ""
    endpoint_name = ""
    endpoint_attributes = []
    rep_endpoint_list = []

    # NEXT_STEPS => Return list of one or more endpoints matching first.last or rep
    for e in endpoint_list:
        endpoint_name = e['name']
        # print('=> {}'.format(endpoint_name))
        if rep_id in endpoint_name:
            # print('\nFound matching entity for rep: {} => {}'.format(rep_id, endpoint_name))
            print('\nFound matching entity for rep: {} => {}: \n{}'.format(rep_id, endpoint_name, json.dumps(e, indent=4)))
            endpoint_id = e['id']
            endpoint_attributes = e['attributes']

    # Set endpoint attribute
    endpoint_attribute = "{}-{}".format(ENDPOINT_ATTRIBUTE_PREFIX, ticket_id)

    #  Run workflow based on workflow type
    if workflow.lower() == 'provision':   
        if endpoint_attribute in endpoint_attributes:
            print('\nEndpoint attribute already exists. Returning')
            return "Endpoint attribute already exists. Returning"             
        endpoint_attributes.append("{}-{}".format(ENDPOINT_ATTRIBUTE_PREFIX, ticket_id))
    elif workflow.lower() == 'provision_new_assignee':        
        # Currently, this does the same thing as if workflow == 'provision'.  Keeping separate in case we want to 
        # add more logic when new assignee is added. 
        endpoint_attributes.append("{}-{}".format(ENDPOINT_ATTRIBUTE_PREFIX, ticket_id))        
    elif workflow.lower() == 'deprovision':        
        print('\nSearching for {} in {}'.format(endpoint_attribute, endpoint_attributes))
        # find index of attribute in list
        if endpoint_attribute in endpoint_attributes:
            endpoint_attribute_index = endpoint_attributes.index(endpoint_attribute)
            print('\nIndex of endpoint attribute: {}'.format(endpoint_attribute_index))
            endpoint_attributes.pop(endpoint_attribute_index)
            print('\nNew endpoint attribute array: {}'.format(endpoint_attributes))
    else:
        return "Failed to update entity attributes for workflow: {}".format(workflow)
    
    print('New Endpoint attributes: {}'.format(endpoint_attributes))

    # Patch URL and Payload
    url = 'https://gateway.production.netfoundry.io/core/v2/endpoints/{}'.format(endpoint_id)

    payload = {
        "attributes": endpoint_attributes
    }

    print('\nNew Payload: {}'.format(json.dumps(payload, indent=4)))

    # Update existing appwan
    res = requests.patch(url, headers=headers, data=json.dumps(payload))
    print('\nResponse from patching existing AppWan: {}'.format(json.dumps(res.json(), indent=4)))


def lookup_rep_entity(bearer_token: str, rep_email: str, network_id: str) -> list[str]:
    url = 'https://gateway.production.netfoundry.io/core/v2/endpoints?networkId={}&size=300&sort=name%2Casc'.format(network_id)
    headers={'Authorization': 'Bearer {}'.format(bearer_token), 'Content-Type': 'application/hal+json'}
    res = requests.get(url, headers=headers).json()
    endpoint_list = res['_embedded']['endpointList']
    # print('Response from lookup_rep_entity: \n{}'.format(json.dumps(endpoint_list, indent=4)))

    rep_id = rep_email.split('@')[0]

    endpoint_id = ""
    endpoint_name = ""
    existing_attributes = ""
    rep_endpoint_list = []

    # NEXT_STEPS => Return list of one or more endpoints matching first.last or rep
    for e in endpoint_list:
        endpoint_name = e['name']
        # print('=> {}'.format(endpoint_name))
        if rep_id in endpoint_name:
            # print('\nFound matching entity for rep: {} => {}'.format(rep_id, endpoint_name))
            print('\nFound matching entity for rep: {} => {}: \n{}'.format(rep_id, endpoint_name, json.dumps(e, indent=4)))
            endpoint_id = e['id']
            existing_attributes = e['attributes']
            return endpoint_name, endpoint_id, existing_attributes
        
    return endpoint_name, endpoint_id, existing_attributes


#####################
# SERVICE_FUNCTIONS #
#####################
def create_service(bearer_token: str, host_id: str, host_ip: str, network_id: str, ticket_id: int, customer_name: str, edge_router_id: str) -> str:
    '''
    SUMMARY: Create new service
    '''
    url = 'https://gateway.production.netfoundry.io/core/v2/services'
    headers={'Authorization': 'Bearer {}'.format(bearer_token), 'Content-Type': 'application/hal+json'}

    print('\nCreating service with attributes: {}'.format("{}-{}".format(ENDPOINT_ATTRIBUTE_PREFIX, ticket_id)))

    payload2_er_hosted = {
        "encryptionRequired": True,
        "modelType": "TunnelerToEdgeRouter",
        "model": {
            "edgeRouterHosts": [
            {
                "edgeRouterId": edge_router_id,
                # "edgeRouterId": NFORYZ_PREFERRED_EDGEROUTER_ID,
                "serverEgress": {
                "protocol": "tcp",
                "host": host_ip,
                "port": 22
                }
            }
            ],
            "clientIngress": {
            "host": "{}.{}.{}".format(host_id, customer_name, ticket_id),
            "port": 22
            },
            "bindEndpointAttributes": [],
            "edgeRouterAttributes": [
            "#all"
            ]
        },
        "attributes": [
            "{}-{}".format(SERVICE_ATTRIBUTE_PREFIX, ticket_id)
        ],
        "name": "ops-tempssh-{}_{}-{}".format(host_id, customer_name, ticket_id),
        "networkId": network_id,
        "edgeRouterAttributes": [
            "#all"
        ]
    }


    res = requests.post(url, headers=headers, data=json.dumps(payload2_er_hosted))
    print('\nCreate service response: \n{}'.format(json.dumps(res.json(), indent=4)))
    return res

def delete_services(bearer_token: str, network_id: str, ticket_id: str):
    url = 'https://gateway.production.netfoundry.io/core/v2/services?networkId={}&size=300&sort=name%2Casc'.format(network_id)
    headers={'Authorization': 'Bearer {}'.format(bearer_token), 'Content-Type': 'application/hal+json'}
    res = requests.get(url, headers=headers).json()
    service_list = res['_embedded']['serviceList']
    
    services_to_delete = []
    print('\nAll Services to delete: ')
    for s in service_list:
        if str(ticket_id) in s['name']:
            print('{} -> {}'.format(s['name'], s['id']))
            services_to_delete.append(s['id'])

    def _delete_service(bearer_token: str, service_id: str):
        try:
            url = 'https://gateway.production.netfoundry.io/core/v2/services/{}'.format(service_id)
            headers={'Authorization': 'Bearer {}'.format(bearer_token), 'Content-Type': 'application/hal+json'}
            res = requests.delete(url, headers=headers)
            res.raise_for_status()
            print('\nResponse for deleting service: \n{}'.format(json.dumps(res.json(), indent=4)))
        except requests.exceptions.HTTPError as errh:
            print('\nERROR => {}'.format(errh))
        
        return res.status_code
    
    print('\nServices to delete array: ')
    for i in services_to_delete:
        print(i)
        status = _delete_service(bearer_token, i)


####################
# APPWAN_FUNCTIONS #
####################
def appwan_exists(bearer_token: str, network_id: str) -> bool:
    url = 'https://gateway.production.netfoundry.io/core/v2/app-wans?networkId={}&page=0&size=100&sort=name,ASC'.format(network_id)
    headers={'Authorization': 'Bearer {}'.format(bearer_token), 'Content-Type': 'application/hal+json'}
    res = requests.get(url, headers=headers).json()
    # print('AppWans: \n{}'.format(json.dumps(res, indent=4)))

    size = res['page']['size']

    if size == 0:
        return False

    appwans = res['_embedded']['appWanList']

    for a in appwans:
        # print('AppWan => {}'.format(json.dumps(a, indent=4)))
        appwan_name = a['name']
        if appwan_name == APPWAN_NAME:
            print('\nFound existing AppWan.  No need to create')
            global APPWAN_ID
            APPWAN_ID = a['id']
            return True

    return False

def create_appwan(bearer_token: str, ticket_id: str, network_id: str):
    url = 'https://gateway.production.netfoundry.io/core/v2/app-wans'
    headers={'Authorization': 'Bearer {}'.format(bearer_token), 'Content-Type': 'application/hal+json'}

    payload = {
        "selected": False,
        "endpointAttributes": [
            "{}-{}".format(ENDPOINT_ATTRIBUTE_PREFIX, ticket_id)
        ],
        "serviceAttributes": [
            "{}-{}".format(SERVICE_ATTRIBUTE_PREFIX, ticket_id)
        ],
        "postureCheckAttributes": [],
        "networkId": network_id,
        "name": APPWAN_NAME
    }

    res = requests.post(url, headers=headers, data=json.dumps(payload)).json()
    print('Results from creating app-wan: \n{}'.format(json.dumps(res, indent=4)))


def update_appwan(bearer_token: str, ticket_id: str, network_id: str, workflow: None|str):
    # get_url = 'https://gateway.production.netfoundry.io/core/v2/app-wans'
    if appwan_exists(bearer_token, network_id):
        print('\nFound existing AppWan {}. Updating with workflow: {}'.format(APPWAN_NAME, workflow))
        url = 'https://gateway.production.netfoundry.io/core/v2/app-wans/{}'.format(APPWAN_ID)
        headers={'Authorization': 'Bearer {}'.format(bearer_token), 'Content-Type': 'application/hal+json'}

        # Call AppWan to get existing attribute list..
        res = requests.get(url, headers=headers).json()

        print('\nExisting AppWan ({}) info: {}'.format(APPWAN_ID, json.dumps(res, indent=4)))

        service_attributes = []
        endpoint_attributes = []
        service_attributes = res['serviceAttributes']
        endpoint_attributes = res['endpointAttributes']

        print('Existing AppWan service attributes: {}'.format(service_attributes))
        print('Existing AppWan endpoint attributes: {}'.format(endpoint_attributes))

        # Append new attributes for new ticket
        if workflow.lower() == 'provision':
            service_attributes.append("{}-{}".format(SERVICE_ATTRIBUTE_PREFIX, ticket_id))
            endpoint_attributes.append("{}-{}".format(ENDPOINT_ATTRIBUTE_PREFIX, ticket_id))
        elif workflow.lower() == 'provision_new_assignee':
            # If workflow set to 'provision_new_assignee' only append the new entity attributes
            endpoint_attributes.append("{}-{}".format(ENDPOINT_ATTRIBUTE_PREFIX, ticket_id))
        elif workflow.lower() == 'deprovision':
            service_attribute = '{}-{}'.format(SERVICE_ATTRIBUTE_PREFIX, ticket_id)
            endpoint_attribute = '{}-{}'.format(ENDPOINT_ATTRIBUTE_PREFIX, ticket_id)
        
            print('\nSearching for {} in {}'.format(service_attribute, service_attributes))
            print('\nSearching for {} in {}'.format(endpoint_attribute, endpoint_attributes))

            if service_attribute in service_attributes and endpoint_attribute in endpoint_attributes:            
                endpoint_attribute_index = endpoint_attributes.index(endpoint_attribute)
                service_attribute_index = service_attributes.index(service_attribute)

                print('\nIndex of endpoint attribute: {}'.format(endpoint_attribute_index))
                print('\nIndex of service attribute: {}'.format(service_attribute_index))

                endpoint_attributes.pop(endpoint_attribute_index)
                service_attributes.pop(service_attribute_index)

                print('\nNew service attribute array: {}'.format(service_attributes))
                print('\nNew endpoint attribute array: {}'.format(endpoint_attributes))
        
        print('\nNew AppWan service attributes: {}'.format(service_attributes))
        print('New AppWan endpoint attributes: {}'.format(endpoint_attributes))

        # PATCH/PUT payload
        patch_payload = {
            "serviceAttributes": service_attributes,
            "endpointAttributes": endpoint_attributes
        }

        # Update existing appwan
        res = requests.patch(url, headers=headers, data=json.dumps(patch_payload))
        print('\nResponse from patching existing AppWan: {}'.format(json.dumps(res.json(), indent=4)))
    else:
        print('\nAppWan with Id: {} does not exists. Nothing to update..'.format(APPWAN_NAME))
        return "AppWan with Id: {} does NOT exist. Nothing to update".format(APPWAN_ID)



def update_appwan_provision(bearer_token: str, ticket_id: str, network_id: str):
    # get_url = 'https://gateway.production.netfoundry.io/core/v2/app-wans'
    url = 'https://gateway.production.netfoundry.io/core/v2/app-wans/{}'.format(APPWAN_ID)
    headers={'Authorization': 'Bearer {}'.format(bearer_token), 'Content-Type': 'application/hal+json'}

    # Call AppWan to get existing attribute list..
    res = requests.get(url, headers=headers).json()

    # print('\nExisting AppWan ({}) info: {}'.format(APPWAN_ID, json.dumps(res, indent=4)))

    service_attributes = []
    endpoint_attributes = []
    service_attributes = res['serviceAttributes']
    endpoint_attributes = res['endpointAttributes']

    print('Existing AppWan service attributes: {}'.format(service_attributes))
    print('Existing AppWan endpoint attributes: {}'.format(endpoint_attributes))

    # Append new attributes for new ticket
    service_attributes.append("{}-{}".format(SERVICE_ATTRIBUTE_PREFIX, ticket_id))
    endpoint_attributes.append("{}-{}".format(ENDPOINT_ATTRIBUTE_PREFIX, ticket_id))

    print('New AppWan service attributes: {}'.format(service_attributes))
    print('New AppWan endpoint attributes: {}'.format(endpoint_attributes))

    # PATCH/PUT payload
    patch_payload = {
        "serviceAttributes": service_attributes,
        "endpointAttributes": endpoint_attributes
    }

    # Update existing appwan
    res = requests.patch(url, headers=headers, data=json.dumps(patch_payload))

    print('\nResponse from patching existing AppWan: {}'.format(json.dumps(res.json(), indent=4)))


def update_appwan_deprovision(bearer_token: str, ticket_id: str, network_id: str):
    """
    Summary: If webhook received for closed ticket, remove the entity attributes and 
    service attributes from the existing appwan
    """
    if appwan_exists(bearer_token, network_id):
        print('\nAppWan {} exists. Updating..'.format(APPWAN_NAME))
        url = 'https://gateway.production.netfoundry.io/core/v2/app-wans/{}'.format(APPWAN_ID)
        headers={'Authorization': 'Bearer {}'.format(bearer_token), 'Content-Type': 'application/hal+json'}

        # Call AppWan to get existing attribute list..
        res = requests.get(url, headers=headers).json()

        print('\nExisting AppWan ({}) info: {}'.format(APPWAN_ID, json.dumps(res, indent=4)))

        service_attributes = []
        endpoint_attributes = []
        service_attributes = res['serviceAttributes']
        endpoint_attributes = res['endpointAttributes']

        print('Existing AppWan service attributes: {}'.format(service_attributes))
        print('Existing AppWan endpoint attributes: {}'.format(endpoint_attributes))

        service_attribute = '{}-{}'.format(SERVICE_ATTRIBUTE_PREFIX, ticket_id)
        endpoint_attribute = '{}-{}'.format(ENDPOINT_ATTRIBUTE_PREFIX, ticket_id)

        print('\nSearching for {} in {}'.format(service_attribute, service_attributes))
        if service_attribute in service_attributes:
            print('Found service_attribute: {}'.format(service_attribute))

        print('\nSearching for {} in {}'.format(endpoint_attribute, endpoint_attributes))
        if endpoint_attribute in endpoint_attributes:
            print('Found endpoint_attribute: {}'.format(endpoint_attribute))

        endpoint_attribute_index = endpoint_attributes.index(endpoint_attribute)
        service_attribute_index = service_attributes.index(service_attribute)

        print('\nIndex of endpoint attribute: {}'.format(endpoint_attribute_index))
        print('\nIndex of service attribute: {}'.format(service_attribute_index))

        endpoint_attributes.pop(endpoint_attribute_index)
        service_attributes.pop(service_attribute_index)

        print('\nNew service attribute array: {}'.format(service_attributes))
        print('\nNew endpoint attribute array: {}'.format(endpoint_attributes))

        # NEXT: Need to make PUT call to update the attributes
            # PATCH/PUT payload
        patch_payload = {
            "serviceAttributes": service_attributes,
            "endpointAttributes": endpoint_attributes
        }

        # Update existing appwan
        res = requests.patch(url, headers=headers, data=json.dumps(patch_payload))

        print('\nResponse from patching existing AppWan: {}'.format(json.dumps(res.json(), indent=4)))

        return "AppWan {} successfully updated".format(APPWAN_NAME)
    else:
        print('\nAppWan with Id: {} does not exists. Nothing to update..'.format(APPWAN_NAME))
        return "AppWan with Id: {} does NOT exist. Nothing to update".format(APPWAN_ID)
    

# def delete_appwan(bearer_token: str):
#     # Get appwan id
#     url = 'https://gateway.production.netfoundry.io/core/v2/app-wans/41152db0-14cb-4134-8218-dc4ad78e68a4'
#     headers={'Authorization': 'Bearer {}'.format(bearer_token), 'Content-Type': 'application/hal+json'}
#     response = requests.request("DELETE", url, headers=headers)
#     print('Delete app-wan: \n{}'.format(json.dumps(response.json(), indent=4)))


##################
# MISC_FUNCTIONS #
##################
def get_zendesk_networkid_form_field(return_network_id_field=True):
    basic = HTTPBasicAuth(ZENDESK_API_USER, ZENDESK_API_TOKEN)
    headers = {'Accept': 'application/json'}
    url = '{}/api/v2/ticket_fields?locale=en-us'.format(NF_ZENDESK_BASE_URL)
    res = requests.get(url, headers=headers, auth=basic).json()
    ticket_fields = res['ticket_fields']

    networkid_field_id = ""
    print('\nSearching Ticket Fields: ')
    for t in ticket_fields:
        title = t['title']
        id = t['id']
        print('Title:ID -> {}: {}'.format(title, id))
        if title == ZENDESK_FORM_NETWORK_FIELD_NAME and return_network_id_field:
            print('\nFound {} ID: {}'.format(title, id))
            networkid_field_id = id
            return networkid_field_id


def get_zendesk_form_field():
    network_field_id = get_zendesk_networkid_form_field()
    basic = HTTPBasicAuth(ZENDESK_API_USER, ZENDESK_API_TOKEN)
    headers = {'Accept': 'application/json'}
    url = '{}/api/v2/ticket_fields/{}.json'.format(NF_ZENDESK_BASE_URL, network_field_id)
    res = requests.get(url, headers=headers, auth=basic).json()
    # print('\nResponse from calling get_zendesk_form_field(): {}'.format(json.dumps(res, indent=4)))

    return res


def update_zendesk_form_networkid_field(network_tuple_list, existing_form_field_data):
    # DOCS => https://developer.zendesk.com/api-reference/ticketing/tickets/ticket_fields/#update-ticket-field
    url = '{}/api/v2/ticket_fields/{}.json'.format(NF_ZENDESK_BASE_URL, ZENDESK_FORM_NETWORK_FIELD_ID)
    basic = HTTPBasicAuth(ZENDESK_API_USER, ZENDESK_API_TOKEN)
    headers = {'Accept': 'application/json'}

    custom_field_options = []

    for n in network_tuple_list:
        print('\nnetwork_name: {}'.format(n[0]))
        print('network_value: {}'.format(n[1]))
        custom_field_option = {
            "id": "",
            "name": n[0],
            "raw_name": n[0],
            "value": n[1],
            "default": False
        }
        # custom_field_options.append(json.dumps(custom_field_option))
        custom_field_options.append(custom_field_option)
    
    # print('\nFinal custom field options list: {}'.format(custom_field_options))
    print('\nFinal custom field options list: ')
    for c in custom_field_options:
        print(json.dumps(c, indent=4))

    # payload = {
    #     "ticket_field": {
    #         "custom_field_options": custom_field_options    
    #     }
    # }

    existing_form_field_data['ticket_field']['custom_field_options'] = custom_field_options
    print('\nNew form field data: {}'.format(json.dumps(existing_form_field_data, indent=4)))

    res = requests.put(url, headers=headers, auth=basic, data=json.dumps(existing_form_field_data))

    print('\nResponse (status: {}) from updating ZenDesk form fields for customer network ids: {}'.format(res.status_code, json.dumps(res.json(), indent=4)))


# def zendesk_main():
#     # get_zendesk_form_field()
#     zitibastions_bearer_token = get_console_bearer_token(NETFOUNDRY_CUSTOMER_CLIENT_ID, NETFOUNDRY_CUSTOMER_CLIENT_SECRET)
#     network_tuple_list = list_networks(bearer_token=zitibastions_bearer_token)
#     existing_form_field_data = get_zendesk_form_field()
#     print('\nResponse from get_zendesk_form_field(): Type: {}; Value: {}'.format(type(existing_form_field_data), json.dumps(existing_form_field_data, indent=4)))
#     update_zendesk_form_networkid_field(network_tuple_list, existing_form_field_data)

# zendesk_main()
# exit()



#################
# MAIN_FUNCTION #
#################
def main():  
    ##############################################################
    # Get Console Access Token for ZitiBastions and Customer Org #
    ##############################################################
    zitibastions_bearer_token = get_console_bearer_token(ZITIBASTIONS_CLIENT_ID, ZITIBASTIONS_CLIENT_SECRET)
    customer_bearer_token = get_console_bearer_token(CUSTOMER_CLIENT_ID, CUSTOMER_CLIENT_SECRET)
    os.environ['ZITIBASTIONS_BEARER_TOKEN'] = zitibastions_bearer_token
    os.environ['CUSTOMER_BEARER_TOKEN'] = customer_bearer_token
    print('\nZITIBASTIONS_BEARER_TOKEN={}'.format(zitibastions_bearer_token))
    print('\nCUSTOMER_BEARER_TOKEN={}'.format(customer_bearer_token))    

    #####################################
    # parse incoming ticket information #
    #####################################
    customer_networkid = incoming_json['ticket']['network_id']
    assignee = incoming_json['ticket']['assignee']
    ticket_id = incoming_json['ticket']['id']
    customer_name = incoming_json['ticket']['customer_name']

    # delete_services(zitibastions_bearer_token, ZITI_BASTION_NETWORKID, ticket_id)
    update_appwan(zitibastions_bearer_token, ticket_id, ZITI_BASTION_NETWORKID, workflow="deprovision")
    update_entity(zitibastions_bearer_token, rep_email=assignee, ticket_id=ticket_id, network_id=ZITI_BASTION_NETWORKID, workflow="deprovision")

    exit()

    ####################################################################
    # Lookup Support Rep Endpoint in ZitiBastions and update attribute #
    ####################################################################
    endpoint_info = lookup_rep_entity(zitibastions_bearer_token, assignee, ZITI_BASTION_NETWORKID) # -> USE_THIS
    print('\nendpoint_info: ', endpoint_info)

    if endpoint_info[0] == "":
        print('Failed to lookup support rep entity id')
        exit()
    # update_entity_attributes(zitibastions_bearer_token, entity_id=endpoint_info[1], ticket_id=ticket_id, attributes=endpoint_info[2])

    ############################
    # Lookup ZitiBastion Hosts #
    ############################
    print('\nCalling get_hosts for network_id: {}'.format(ZITI_BASTION_NETWORKID))
    bastion_host_urls = get_network_host_urls(zitibastions_bearer_token, ZITI_BASTION_NETWORKID)
    zb_hosts_url = bastion_host_urls[0]
    zb_controller_url = bastion_host_urls[1]
    zb_edgerouter_url = bastion_host_urls[2]

    zb_hosts_dict = get_hosts(zitibastions_bearer_token, zb_hosts_url)
    print('\nZitiBastions host url: {}'.format(zb_hosts_url))
    pprint(zb_hosts_dict)

    #########################
    # Lookup Customer Hosts #
    #########################
    print('\nCalling get_hosts for network_id: {}'.format(customer_networkid))
    cust_host_urls = get_network_host_urls(customer_bearer_token, customer_networkid)
    cust_hosts_url = cust_host_urls[0]
    cust_controller_url = cust_host_urls[1]
    cust_edgerouter_url = cust_host_urls[2]

    cust_hosts_dict = get_hosts(customer_bearer_token, cust_hosts_url)
    print('\nCustomer host url: {}'.format(cust_hosts_url))
    pprint(cust_hosts_dict)

    ############################################
    # Create Individual Services for All Hosts #
    ############################################
    # PARAMS => bearer_token: str, host_id: str, host_ip: str, network_id: str, ticket_id: str, customer_name: str) -> str:
    for h in cust_hosts_dict:
        host_id = h
        host_ip = cust_hosts_dict[h]
        print('Creating service for  => {}, {}'.format(h, cust_hosts_dict[h]))
        create_service(zitibastions_bearer_token, 
                       host_id, 
                       host_ip, 
                       ZITI_BASTION_NETWORKID, 
                       ticket_id, 
                       customer_name,
                       ZITI_BASTIONS_PREFERRED_EDGEROUTER_ID
                       )

    #############################################
    # Check if AppWan exists; if not; create it #
    #############################################
    exists = appwan_exists(zitibastions_bearer_token, ZITI_BASTION_NETWORKID)
    print('\nResult of appwan_exists() => {}'.format(exists))
    if not exists:
        print('\nAppWan does not exist: Creating..')
        create_appwan(zitibastions_bearer_token, ticket_id=ticket_id, network_id=ZITI_BASTION_NETWORKID)
    else:
        print('\nFound existing AppWan. Updating with new endpoint/service attributes')
        update_appwan_provision(zitibastions_bearer_token, ticket_id=ticket_id, network_id=ZITI_BASTION_NETWORKID)

    # 7. Test SSH to edge router server IP
    # PLACEHOLDER

main()