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

def sync_dns_records(data, zone_id, headers):
    # Delete existing DNS records for the subdomain (if editing an existing subdomain)
    response = requests.get(f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?name={data["subdomain"]}.{data["domain"]}', headers=headers)
    existing_records = response.json()
    if response.status_code == 200 and existing_records['success']:
        for record in existing_records['result']:
            # Skip records created by Discord
            if "discord" in record["name"]:
                continue
            delete_response = requests.delete(f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record["id"]}', headers=headers)
            if delete_response.status_code == 200:
                print(f'Successfully deleted record {record["id"]}')
            else:
                print(f'Failed to delete record {record["id"]}: {delete_response.text}')

    # Create new DNS records
    for record_type, values in data['records'].items():
        for value in values:
            payload = {
                'type': record_type,
                'name': f"{data['subdomain']}.{data['domain']}",
                'content': value,
                'proxied': data['proxied']
            }
            response = requests.post(f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records', headers=headers, json=payload)
            if response.status_code == 200:
                print(f'Successfully created {record_type} record for {data["subdomain"]}.{data["domain"]}')
            else:
                print(f'Failed to create {record_type} record for {data["subdomain"]}.{data["domain"]}: {response.text}')

def deploy_subdomain(subdomain_file):
    with open(subdomain_file, 'r') as f:
        data = json.load(f)

    cf_api_token = os.getenv('CF_API_TOKEN')
    headers = {
        'Authorization': f'Bearer {cf_api_token}',
        'Content-Type': 'application/json'
    }

    zone_id = get_zone_id(data['domain'], headers)
    sync_dns_records(data, zone_id, headers)

if __name__ == '__main__':
    domains_folder = 'domains'
    existing_files = set(os.listdir(domains_folder))
    deployed_subdomains = {f.replace('.json', '') for f in existing_files}

    # Deploy new or updated subdomains
    for subdomain_file in existing_files:
        subdomain_file_path = os.path.join(domains_folder, subdomain_file)
        deploy_subdomain(subdomain_file_path)

    # Check for deleted subdomains and clean up
    response = requests.get(f'https://api.cloudflare.com/client/v4/zones?name=is-app.top', headers=headers)
    result = response.json()
    if response.status_code == 200 and result['success']:
        zone_id = result['result'][0]['id']
        response = requests.get(f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records', headers=headers)
        existing_records = response.json()
        if response.status_code == 200 and existing_records['success']:
            for record in existing_records['result']:
                subdomain = record["name"].split('.')[0]
                if subdomain not in deployed_subdomains and "discord" not in record["name"]:
                    delete_response = requests.delete(f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record["id"]}', headers=headers)
                    if delete_response.status_code == 200:
                        print(f'Successfully deleted record {record["id"]}')
                    else:
                        print(f'Failed to delete record {record["id"]}: {delete_response.text}')
    else:
        print(f"Failed to get zone ID for is-app.top: {result}")
        exit(1)
