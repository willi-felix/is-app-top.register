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

def delete_subdomain(subdomain, domain, headers):
    # Xóa các bản ghi DNS cho subdomain
    zone_id = get_zone_id(domain, headers)
    response = requests.get(f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?name={subdomain}.{domain}', headers=headers)
    existing_records = response.json()
    if response.status_code == 200 and existing_records['success']:
        for record in existing_records['result']:
            if "discord" in record["name"]:
                continue
            delete_response = requests.delete(f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record["id"]}', headers=headers)
            if delete_response.status_code == 200:
                print(f'Successfully deleted record {record["id"]}')
            else:
                print(f'Failed to delete record {record["id"]}: {delete_response.text}')

if __name__ == '__main__':
    domains_folder = 'domains'
    current_subdomains = {f.replace('.json', '') for f in os.listdir(domains_folder)}

    cf_api_token = os.getenv('CF_API_TOKEN')
    headers = {
        'Authorization': f'Bearer {cf_api_token}',
        'Content-Type': 'application/json'
    }

    # Kiểm tra và xóa các subdomains không còn tồn tại dưới dạng tệp JSON
    response = requests.get(f'https://api.cloudflare.com/client/v4/zones?name=is-app.top', headers=headers)
    result = response.json()
    if response.status_code == 200 and result['success']:
        zone_id = result['result'][0]['id']
        response = requests.get(f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records', headers=headers)
        existing_records = response.json()
        if response.status_code == 200 and existing_records['success']:
            for record in existing_records['result']:
                subdomain = record["name"].split('.')[0]
                if subdomain not in current_subdomains and "discord" not in record["name"]:
                    delete_response = requests.delete(f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record["id"]}', headers=headers)
                    if delete_response.status_code == 200:
                        print(f'Successfully deleted record {record["id"]}')
                    else:
                        print(f'Failed to delete record {record["id"]}: {delete_response.text}')
    else:
        print(f"Failed to get zone ID for is-app.top: {result}")
        exit(1)
