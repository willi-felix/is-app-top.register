import os
import json
import requests

def get_zone_id(domain, headers):
    response = requests.get(f'https://api.cloudflare.com/client/v4/zones?name={domain}', headers=headers)
    result = response.json()
    if response.status_code == 200 and result['success']:
        return result['result'][0]['id']
    else:
        print(f"Failed to get zone ID for {domain}: {result}")
        exit(1)

def delete_subdomain(subdomain_file):
    with open(subdomain_file, 'r') as f:
        data = json.load(f)

    cf_api_token = os.getenv('CF_API_TOKEN')
    headers = {
        'Authorization': f'Bearer {cf_api_token}',
        'Content-Type': 'application/json'
    }

    zone_id = get_zone_id(data['domain'], headers)

    # Delete existing DNS records for the subdomain
    response = requests.get(f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?name={data["subdomain"]}.{data["domain"]}', headers=headers)
    existing_records = response.json()
    if response.status_code == 200 and existing_records['success']:
        for record in existing_records['result']:
            delete_response = requests.delete(f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record["id"]}', headers=headers)
            if delete_response.status_code == 200:
                print(f'Successfully deleted record {record["id"]}')
            else:
                print(f'Failed to delete record {record["id"]}: {delete_response.text}')

if __name__ == '__main__':
    subdomain_file = 'domains/{subdomain}.json'  # Replace with the actual path to the subdomain file
    delete_subdomain(subdomain_file)
