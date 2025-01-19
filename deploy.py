import os
import json
import requests

def get_zone_id(domain, headers):
    # Lấy ID của zone dựa trên tên miền
    response = requests.get(f'https://api.cloudflare.com/client/v4/zones?name={domain}', headers=headers)
    result = response.json()
    if response.status_code == 200 and result['success']:
        return result['result'][0]['id']
    else:
        print(f"Failed to get zone ID for {domain}: {result}")
        exit(1)

def check_and_sync_dns_records(data, zone_id, headers):
    # Kiểm tra và đồng bộ các bản ghi DNS
    subdomain_full_name = f"{data['subdomain']}.{data['domain']}"
    
    # Kiểm tra các bản ghi DNS hiện có cho subdomain
    response = requests.get(f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?name={subdomain_full_name}', headers=headers)
    existing_records = response.json()
    
    # Nếu có bản ghi hiện tại, xóa các bản ghi đó
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
    
    # Triển khai các bản ghi DNS mới
    for record_type, values in data['records'].items():
        for value in values:
            payload = {
                'type': record_type,
                'name': subdomain_full_name,
                'content': value,
                'proxied': data['proxied']
            }
            response = requests.post(f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records', headers=headers, json=payload)
            if response.status_code == 200:
                print(f'Successfully created {record_type} record for {subdomain_full_name}')
            else:
                print(f'Failed to create {record_type} record for {subdomain_full_name}: {response.text}')

def deploy_subdomain(subdomain_file):
    # Triển khai subdomain từ tệp JSON
    with open(subdomain_file, 'r') as f:
        data = json.load(f)
    
    cf_api_token = os.getenv('CF_API_TOKEN')
    headers = {
        'Authorization': f'Bearer {cf_api_token}',
        'Content-Type': 'application/json'
    }

    zone_id = get_zone_id(data['domain'], headers)
    check_and_sync_dns_records(data, zone_id, headers)

if __name__ == '__main__':
    domains_folder = 'domains'
    existing_files = set(os.listdir(domains_folder))
    deployed_subdomains = {f.replace('.json', '') for f in existing_files}

    # Triển khai mới hoặc cập nhật subdomains
    for subdomain_file in existing_files:
        subdomain_file_path = os.path.join(domains_folder, subdomain_file)
        deploy_subdomain(subdomain_file_path)

    # Kiểm tra và xóa các subdomains không còn tồn tại dưới dạng tệp JSON
    cf_api_token = os.getenv('CF_API_TOKEN')
    headers = {
        'Authorization': f'Bearer {cf_api_token}',
        'Content-Type': 'application/json'
    }
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
