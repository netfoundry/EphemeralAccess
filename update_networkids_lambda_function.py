import json
import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

ZENDESK_API_USER=os.getenv('ZENDESK_API_USER')
ZENDESK_API_TOKEN=os.getenv('ZENDESK_API_TOKEN')
MOP_GLOBAL_CLIENT_ID=os.getenv('MOP_GLOBAL_CLIENT_ID')
MOP_GLOBAL_CLIENT_SECRET=os.getenv('MOP_GLOBAL_CLIENT_SECRET')
NF_ZENDESK_BASE_URL='https://netfoundry.zendesk.com'
ZENDESK_FORM_NETWORK_FIELD_NAME="ziti_network_id"
ZENDESK_FORM_NETWORK_FIELD_ID="18522170008973"

def lambda_handler(event, context):
    # TODO implement
    zitibastions_bearer_token = get_console_bearer_token(MOP_GLOBAL_CLIENT_ID, MOP_GLOBAL_CLIENT_SECRET)
    network_tuple_list = list_networks(bearer_token=zitibastions_bearer_token)
    existing_form_field_data = get_zendesk_form_field()
    print('\nResponse from get_zendesk_form_field(): Type: {}; Value: {}'.format(type(existing_form_field_data), json.dumps(existing_form_field_data, indent=4)))
    rc = update_zendesk_form_networkid_field(network_tuple_list, existing_form_field_data)
    
    if rc == 200 or rc == 201 or rc == 202:
        return {
            'statusCode': 200,
            'body': json.dumps('You have successfully updated the ZenDesk form custom network_id field')
        }
    else:
        return {
            'statusCode': 500,
            'body': json.dumps('Something went wrong updating the ZenDesk form custom network_id field')
        }
 
    
def get_console_bearer_token(client_id, client_secret) -> str:
    # print('\nCalling get_console_bearer_token() with clientId: {}, and clientSecret: {}'.format(client_id, client_secret))
    url = 'https://netfoundry-production-xfjiye.auth.us-east-1.amazoncognito.com/oauth2/token'

    payload = 'grant_type=client_credentials&client_id={}'.format(client_id)
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    res = requests.post(url, headers=headers, data=payload, auth=(client_id, client_secret)).json()
    print('\nResponse from get_token: {}'.format(json.dumps(res, indent=4)))

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

    # print('\nAll Network Tuples: ')
    network_tuple_list = []    
    for n in network_list:  
        network_tuple = (n['name'], n['id'])
        network_status = n['status']
        # print('{} -> {}: STATUS: {}'.format(network_tuple, network_status))                 
        if network_status == 'PROVISIONED':                    
            network_tuple_list.append(network_tuple)
        
    print('\nFinal network_tuple_list for all PROVISIONED networks: ') 
    count = 0
    for n in network_tuple_list:
        print('{} -> {}'.format(count, n))
        count += 1

    # network_tuple_list.pop(0)

    return network_tuple_list

def update_zendesk_form_networkid_field(network_tuple_list, existing_form_field_data) -> int:
    # DOCS => https://developer.zendesk.com/api-reference/ticketing/tickets/ticket_fields/#update-ticket-field
    url = '{}/api/v2/ticket_fields/{}.json'.format(NF_ZENDESK_BASE_URL, ZENDESK_FORM_NETWORK_FIELD_ID)
    # url = 'https://httpbin.org/put'
    basic = HTTPBasicAuth(ZENDESK_API_USER, ZENDESK_API_TOKEN)
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

    custom_field_options = []

    for n in network_tuple_list:
        # print('\nnetwork_name: {}'.format(n[0]))
        # print('network_value: {}'.format(n[1]))
        custom_field_option = {
            "id": "",
            "name": n[0],
            "raw_name": n[0],
            "value": n[1],
            "default": False
        }
        # custom_field_options.append(json.dumps(custom_field_option))
        custom_field_options.append(custom_field_option)
    
    print('\nFinal custom field options list: ')
    for c in custom_field_options:
        print(json.dumps(c, indent=4))

    existing_form_field_data['ticket_field']['custom_field_options'] = custom_field_options
    print('\nNew form field data: {}'.format(json.dumps(json.dumps(existing_form_field_data, indent=4))))

    # res = requests.put(url, headers=headers, auth=basic, json=json.dumps(existing_form_field_data))
    res = requests.put(url, headers=headers, auth=basic, json=existing_form_field_data)

    print('\nResponse (status: {}) from updating ZenDesk form fields for customer network ids: {}'.format(res.status_code, json.dumps(res.json(), indent=4)))

    return res.status_code

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


# main()