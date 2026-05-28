import requests

# Get token
resp = requests.post('http://localhost:8000/api/accounts/users/login/', json={
    'username': 'manager@test.local',
    'password': 'Pass@123',
})
print("Login response:", resp.status_code)
data = resp.json()
print("User tenant:", data.get('user', {}).get('tenant'))

token = data['tokens']['access']
tenant_schema = data['user']['tenant']['schema_name'] if data['user'].get('tenant') else None
print("Tenant schema:", tenant_schema)

headers = {
    'Authorization': f'Bearer {token}',
    'X-Tenant': tenant_schema or '',
}
print("\nHeaders:", headers)

# Test campaigns with tenant header
r = requests.get('http://localhost:8000/api/dialer-campaign/campaigns/', headers=headers)
print(f"\nCampaigns: {r.status_code}")
if r.status_code == 200:
    print(r.json())
else:
    # Extract error
    import re
    match = re.search(r'<pre class="exception_value">(.*?)</pre>', r.text, re.DOTALL)
    if match:
        print("Error:", match.group(1).strip())
    else:
        print(r.text[:500])
