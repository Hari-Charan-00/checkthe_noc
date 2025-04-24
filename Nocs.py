import requests
import pandas as pd
import urllib3

#urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = ""
SECRET = ''  # Add your secret here
KEY = ''     # Add your key here

Partner_IDS = [""]

Partner_Names = {
    "": "ABC1"
}

Client_IDS = []
Client_Names = []
Noc_Names = []
Partner_Names_List = []

def token_generation():
    try:
        token_url = BASE_URL + "auth/oauth/token"
        auth_data = {
            'client_secret': SECRET,
            'grant_type': 'client_credentials',
            'client_id': KEY
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        token_response = requests.post(token_url, data=auth_data, headers=headers, verify=True)
        
        if token_response.status_code == 200:
            token_data = token_response.json()
            access_token = token_data.get('access_token')
            return access_token
        else:
            print("Failed to obtain access token:", token_response.text)
            return None
    except Exception as e:
        print("An error occurred during token generation:", str(e))
        return None
    
def fetch_clients(access_token, partner_id):
    clients = []
    page = 1
    
    while True:
        try:
            auth_header = {'Authorization': 'Bearer ' + access_token, 'Content-Type': 'application/json'}
            client_ids_url = BASE_URL + f"api/v2/tenants/{partner_id}/clients/search?pageNo={page}&pageSize=100"
            response = requests.get(client_ids_url, headers=auth_header, verify=True)
            
            if response.status_code == 407 or "invalid_token" in response.text.lower():
                print("Token invalid or expired. Generating a new token...")
                access_token = token_generation()
                if not access_token:
                    print("Unable to generate a new token. Exiting.")
                    break
                continue  # Retry with the new token

            if response.status_code == 200:
                clients_data = response.json()
                results = clients_data.get('results', [])
                clients.extend(results)

                # Check if there is a next page
                total_pages = clients_data.get('totalPages', 1)
                if page >= total_pages:
                    break
                page += 1
                
            else:
                print("Bad API response, unable to get client IDs")
                break
        except Exception as e:
            print("An error occurred:", str(e))
            break

    return clients

def get_noc_name(access_token):
    if access_token:
        for partner_id in Partner_IDS:
            partner_name = Partner_Names.get(partner_id, "Unknown Partner")
            print(f"Processing partner: {partner_name}")
            
            clients = fetch_clients(access_token, partner_id)
            for client in clients:
                client_id = client.get('uniqueId')
                client_name = client.get('name')
                if client_id and client_name:
                    Client_IDS.append(client_id)
                    Client_Names.append(client_name)
                    Partner_Names_List.append(partner_name)
                
                try:
                    auth_header = {'Authorization': 'Bearer ' + access_token, 'Content-Type': 'application/json'}
                    noc_details_url = BASE_URL + f"api/v2/tenants/{partner_id}/clients/{client_id}"
                    response = requests.get(noc_details_url, headers=auth_header, verify=True)
                    
                    if response.status_code == 407 or "invalid_token" in response.text.lower():
                        print("Token invalid or expired. Generating a new token...")
                        access_token = token_generation()
                        if not access_token:
                            print("Unable to generate a new token. Exiting.")
                            break
                        continue  # Retry with the new token
                    
                    if response.status_code == 200:
                        noc_data = response.json()
                        noc_details = noc_data.get('nocDetails', {})
                        noc_name = noc_details.get('name', 'N/A')
                        Noc_Names.append(noc_name)
                    else:
                        print("Unable to get the Noc details.")
                except Exception as e:
                    print("An error occurred:", str(e))
    else:
        print("Unable to get the access token, retrying again")
        access_token = token_generation()
        if access_token:
            get_noc_name(access_token)

def save_to_excel():
    data = {
        "Partner Name": Partner_Names_List,
        "Client Name": Client_Names,
        "NOC Name": Noc_Names
    }
    df = pd.DataFrame(data)
    df.to_excel("AllCovered_noc_detailss.xlsx", index=False)
    print("Data saved to AllCovered_noc_detailss.xlsx")

access_token = token_generation()
if access_token:
    get_noc_name(access_token)
    save_to_excel()
else:
    print("Failed to obtain access token.")
