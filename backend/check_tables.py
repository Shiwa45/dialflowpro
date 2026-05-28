import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

import django
django.setup()

from django.db import connection
from apps.tenants.models import Tenant

tenant = Tenant.objects.get(schema_name='test_tenant')
print(f"Tenant: {tenant.name} ({tenant.schema_name})")

# Try setting the tenant on the connection
connection.set_tenant(tenant)
print(f"Schema after set_tenant: {connection.schema_name}")

# Try querying
from apps.dialer_campaign.models import Campaign
campaigns = Campaign.objects.all()
print(f"Campaigns found: {campaigns.count()}")
for c in campaigns:
    print(f"  - {c.name} (status={c.status})")
