#!/bin/bash
set -e

VENV=/opt/dialflow-venv
PROJECT=/mnt/c/Users/easyian/dialflow/backend

source $VENV/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.development
cd $PROJECT

echo "=== Creating public tenant ==="
python manage.py shell << 'PYEOF'
from apps.tenants.models import Tenant, Domain

if not Tenant.objects.filter(schema_name='public').exists():
    t = Tenant(schema_name='public', name='DialFlow Public')
    t.save()
    print(f"Tenant created: {t.name}")
else:
    t = Tenant.objects.get(schema_name='public')
    print(f"Tenant already exists: {t.name}")

if not Domain.objects.filter(domain='localhost').exists():
    d = Domain(domain='localhost', tenant=t, is_primary=True)
    d.save()
    print(f"Domain created: {d.domain}")
else:
    print("Domain localhost already exists")
PYEOF

echo ""
echo "=== Creating superuser ==="
python manage.py shell << 'PYEOF'
from apps.accounts.models import User

if not User.objects.filter(username='admin').exists():
    u = User.objects.create_superuser(
        username='admin',
        email='admin@dialflow.local',
        password='Admin@123',
        role=1,
    )
    print(f"Superuser created: {u.username} / Admin@123")
else:
    print("Superuser 'admin' already exists")
PYEOF

echo ""
echo "=== Setup complete! ==="
echo ""
echo "  Admin URL : http://localhost:8000/admin"
echo "  Username  : admin"
echo "  Password  : Admin@123"
