import json
import requests
from pprint import pprint
import os


ZITIBASTIONS_CLIENT_SECRET = os.environ.get('ZITIBASTIONS_CLIENT_SECRET')
ZITIBASTIONS_CLIENT_ID = os.environ.get('ZITIBASTIONS_CLIENT_ID')
ZITI_BASTIONS_PREFERRED_EDGEROUTER_NAME = os.environ.get('ZITI_BASTIONS_PREFERRED_EDGEROUTER_NAME')
ZITI_BASTIONS_PREFERRED_EDGEROUTER_ID = os.environ.get('ZITI_BASTIONS_PREFERRED_EDGEROUTER_ID')
ZITI_BASTIONS_PREFERRED_EDGEROUTER_HOSTID = os.environ.get('ZITI_BASTIONS_PREFERRED_EDGEROUTER_HOSTID')
ZITI_BASTION_NETWORKID = os.environ.get('ZITI_BASTION_NETWORKID')
SERVICE_ATTRIBUTE_PREFIX = os.environ.get('SERVICE_ATTRIBUTE_PREFIX')
OPS_SERVER_ENDPOINT_NAME = os.environ.get('OPS_SERVER_ENDPOINT_NAME')
NFORYZ_PREFERRED_EDGEROUTER_ID = os.environ.get('NFORYZ_PREFERRED_EDGEROUTER_ID')
ENTITY_ATTRIBUTE = os.environ.get('ENTITY_ATTRIBUTE')
ENDPOINT_ATTRIBUTE_PREFIX = os.environ.get('ENDPOINT_ATTRIBUTE_PREFIX')
CUSTOMER_CLIENT_SECRET = os.environ.get('CUSTOMER_CLIENT_SECRET')
CUSTOMER_CLIENT_ID = os.environ.get('CUSTOMER_CLIENT_ID')
CSLAB_PREFERRED_EDGEROUTER_ID = os.environ.get('CSLAB_PREFERRED_EDGEROUTER_ID')
CS_LAB_NETWORK_ID = os.environ.get('CS_LAB_NETWORK_ID')
APPWAN_NAME = os.environ.get('APPWAN_NAME')
# ZENDESK
ZENDESK_FORM_NETWORK_FIELD_NAME="ziti_network_id"
ZENDESK_FORM_NETWORK_FIELD_ID="18522170008973"


# def call_httpbin():
#     res = requests.get('http://httpbin.org/get')
#     # print('\nResponse from httpbin test: {}'.format(json.dumps(res)))
#     return res.json()


def lambda_handler(event, context):    
    ##############################################################
    # Get Console Access Token for ZitiBastions and Customer Org #
    ##############################################################
    zitibastions_bearer_token = get_console_bearer_token(ZITIBASTIONS_CLIENT_ID, ZITIBASTIONS_CLIENT_SECRET)
    customer_bearer_token = get_console_bearer_token(CUSTOMER_CLIENT_ID, CUSTOMER_CLIENT_SECRET)
    
    #####################################
    # parse incoming ticket information #
    #####################################
    data = json.loads(event['body'])
    print('\nIncoming JSON body: ', json.dumps(data, indent=4))
    customer_networkid = data['ticket']['network_id']
    assignee_email = data['ticket']['assignee_email']
    ticket_id = data['ticket']['id']
    STATUS = data['ticket']['status']
    customer_domain_name = data['ticket']['requester_email'].split("@")[1].split(".")[0]
    
    if STATUS.lower() == 'open' or STATUS.lower() == 'new':
        print('Status: open')
        
        ####################################################################
        # Lookup Support Rep Endpoint in ZitiBastions and update attribute #
        ####################################################################
        update_entity(zitibastions_bearer_token, assignee_email=assignee_email, ticket_id=ticket_id, network_id=ZITI_BASTION_NETWORKID, workflow="provision")
        
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
        # PARAMS => bearer_token: str, host_id: str, host_ip: str, network_id: str, ticket_id: str, customer_domain_name: str) -> str:
        for h in cust_hosts_dict:
            host_id = h
            host_ip = cust_hosts_dict[h]
            print('Creating service for  => {}, {}'.format(h, cust_hosts_dict[h]))
            create_service(zitibastions_bearer_token, 
                          host_id, 
                          host_ip, 
                          ZITI_BASTION_NETWORKID, 
                          ticket_id, 
                          customer_domain_name,
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
            update_appwan(zitibastions_bearer_token, ticket_id=ticket_id, network_id=ZITI_BASTION_NETWORKID, workflow="provision")
        
    elif STATUS.lower() == 'assignee_changed':
        '''
        Execute this section if the ticket assignee changed or a new assignee added. 
        For now, don't deprovision the original agent, add the new agent (entity attributes)
        to existing AppWan and Services.. 
        
        Step 1: 
          - Lookup new assignee entity, and update the entity with the new entity attribute 
            EntityName: 
            - "{}-{}".format(ENDPOINT_ATTRIBUTE_PREFIX, ticket_id)
        
        Step 2: 
          - Lookup existing AppWan; and update with new entity attribute. 

        QUESTION: 
          - Can we leverage existing functions: update_entity(), and update_appwan()
          Answer: 
            - Yes, just keep the 'workflow' as 'provision_new_assignee'
        '''
        ###################
        # Update Endpoint #
        ###################
        update_entity(zitibastions_bearer_token, assignee_email=assignee_email, ticket_id=ticket_id, network_id=ZITI_BASTION_NETWORKID, workflow="provision_new_assignee")

        ##################
        # Update AppWan  #
        ##################
        update_appwan(zitibastions_bearer_token, ticket_id=ticket_id, network_id=ZITI_BASTION_NETWORKID, workflow="provision_new_assignee")
    
    elif STATUS.lower() == 'closed' or STATUS.lower() == 'solved':
        print('\nStatus: closed')

        ###################
        # Update Endpoint #
        ###################
        update_entity(zitibastions_bearer_token, assignee_email=assignee_email, ticket_id=ticket_id, network_id=ZITI_BASTION_NETWORKID, workflow="deprovision")

        ##################
        # Delete service #
        ##################
        delete_services(zitibastions_bearer_token, ZITI_BASTION_NETWORKID, ticket_id)

        ##################
        # Update AppWan  #
        ##################
        update_appwan(zitibastions_bearer_token, ticket_id=ticket_id, network_id=ZITI_BASTION_NETWORKID, workflow="deprovision")
         
    else:
        print('\nError with Ticket status..')

        return {
        'statusCode': 500,
        'body': {
            'status': 'Failed to run lambda function to provision/deprovision temp ssh access'
        }
    }
    
    return {
        'statusCode': 200,
        'body': {
            'status': 'success'
        }
    }


# Generate Bearer token
def get_console_bearer_token(client_id, client_secret) -> str:
    url = 'https://netfoundry-production-xfjiye.auth.us-east-1.amazoncognito.com/oauth2/token'
    payload = 'grant_type=client_credentials&client_id={}'.format(client_id)
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    
    response = requests.post(url, headers=headers, data=payload, auth=(client_id, client_secret)).json()
    access_token = response['access_token']

    return access_token


# List networks
def list_networks(bearer_token: str):
    url = 'https://gateway.production.netfoundry.io/core/v2/networks'
    headers={'Authorization': 'Bearer {}'.format(bearer_token), 'Content-Type': 'application/hal+json'}
    res = requests.get(url=url, headers=headers).json()

    network_list = res['_embedded']['networkList']
    
    # print('\nResponse from calling get networks: {}'.format(json.dumps(res['_embedded']['networkList'], indent=4)))
    for n in network_list:
        print('\nNetwork: {}'.format(json.dumps(n, indent=4)))


# Get network
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
    

# Get hosts
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
def create_entity(bearer_token: str, assignee_email: str, network_id: str):
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
        "name": "support.temp.access.endpoint.{}".format(assignee_email)
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    print('Create Entity Response: \n{}'.format(json.dumps(response.json(), indent=4)))


def update_entity(bearer_token: str, assignee_email: str, ticket_id: str, network_id: str, workflow: None|str):    
    # First, lookup the current entity:
    print('\nCalling update_entity() for {}'.format(assignee_email))
    url = 'https://gateway.production.netfoundry.io/core/v2/endpoints?networkId={}&size=300&sort=name%2Casc'.format(network_id)
    headers={'Authorization': 'Bearer {}'.format(bearer_token), 'Content-Type': 'application/hal+json'}
    res = requests.get(url, headers=headers).json()
    endpoint_list = res['_embedded']['endpointList']
    # print('Response from lookup_rep_entity: \n{}'.format(json.dumps(endpoint_list, indent=4)))

    rep_id = assignee_email.split('@')[0]
    print('\nSearching for entity for rep_id: {0}'.format(rep_id))

    endpoint_id = ""
    endpoint_name = ""
    endpoint_attributes = []
    rep_endpoint_list = []

    # NEXT_STEPS => Return list of one or more endpoints matching first.last or rep
    for e in endpoint_list:
        endpoint_name = e['name']
        print('=> {}'.format(endpoint_name))
        if rep_id.lower() in endpoint_name.lower():
            # print('\nFound matching entity for rep: {} => {}'.format(rep_id, endpoint_name))
            print('\nFound matching entity for rep: {} => {}: \n{}'.format(rep_id, endpoint_name, json.dumps(e, indent=4)))
            endpoint_id = e['id']
            endpoint_attributes = e['attributes']
            # if only want to update the first entity return here

    # Set endpoint attribute
    endpoint_attribute = "{}-{}".format(ENDPOINT_ATTRIBUTE_PREFIX, ticket_id)

    #  Run workflow based on workflow type
    if workflow.lower() == 'provision':   
        if endpoint_attribute in endpoint_attributes:
            print('\nEndpoint attribute already exists. Returning')
            return "Endpoint attribute already exists. Returning"             
        endpoint_attributes.append("{}-{}".format(ENDPOINT_ATTRIBUTE_PREFIX, ticket_id))
    elif workflow.lower() == 'provision_new_assignee': 
        print('\nExecuting workflow {}'.format(workflow))       
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
    print('\nResponse from patching existing Entity: {}'.format(json.dumps(res.json(), indent=4)))

    # if res.status_code != 200 or res.status_code != 201:
    #     print('\nERROR :: Failed to update existing entity.  Exiting.')
    #     exit()

    return res.status_code


#####################
# SERVICE_FUNCTIONS #
#####################
def create_service(bearer_token: str, host_id: str, host_ip: str, network_id: str, ticket_id: int, customer_domain_name: str, edge_router_id: str) -> str:
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
            "host": "{}.{}.{}".format(host_id, customer_domain_name, ticket_id),
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
        "name": "ops-tempssh-{}_{}-{}".format(host_id, customer_domain_name, ticket_id),
        "networkId": network_id,
        "edgeRouterAttributes": [
            "#all"
        ]
    }


    res = requests.post(url, headers=headers, data=json.dumps(payload2_er_hosted))
    print('\nCreate service response: \n{}'.format(json.dumps(res.json(), indent=4)))
    return res


# Delete services
def delete_services(bearer_token: str, network_id: str, ticket_id: str):
    """
    Summary: Delete any services tied to ticket_id param
    """
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


# Create appwan
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
