import re

with open('backend/apps/callcenter/consumers.py', 'r') as f:
    content = f.read()

# Add the tenant_db_sync decorator after imports
decorator_code = '''
from django_tenants.utils import schema_context

def tenant_db_sync(func):
    def wrapper(self, *args, **kwargs):
        schema = getattr(self, 'tenant_name', 'public') or 'public'
        with schema_context(schema):
            return func(self, *args, **kwargs)
    return database_sync_to_async(wrapper)
'''

content = content.replace('import json', 'import json\\n' + decorator_code)

# Replace all @database_sync_to_async with @tenant_db_sync
content = content.replace('@database_sync_to_async', '@tenant_db_sync')

# Inject self.tenant_name parsing into connect methods
connect_injection = '''
        query_string = self.scope.get('query_string', b'').decode()
        params = dict(p.split('=', 1) for p in query_string.split('&') if '=' in p)
        self.tenant_name = params.get('tenant')
'''

# We need to inject this into the beginning of connect() for all consumers.
# We can find     async def connect(self): and insert it.
content = content.replace('    async def connect(self):', '    async def connect(self):\\n' + connect_injection)

with open('backend/apps/callcenter/consumers.py', 'w') as f:
    f.write(content)
print("Updated consumers.py successfully!")
