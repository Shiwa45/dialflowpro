#!/bin/bash
set -e

VENV=/opt/dialflow-venv
PROJECT=/mnt/c/Users/easyian/dialflow/backend

source $VENV/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.development
cd $PROJECT

echo "=== Cleaning up previously generated migrations ==="
# Delete all migration files except __init__.py
find apps -path "*/migrations/0*.py" -delete 2>/dev/null || true
echo "Old migrations deleted."

echo ""
echo "=== Making fresh migrations in dependency order ==="

# Shared schema apps first (no cross-app deps except common)
python manage.py makemigrations tenants 2>&1
python manage.py makemigrations common 2>&1
python manage.py makemigrations dialer_settings 2>&1
python manage.py makemigrations accounts 2>&1

# Tenant apps (can depend on shared accounts/common)
python manage.py makemigrations dialer_gateway 2>&1
python manage.py makemigrations dialer_contact 2>&1
python manage.py makemigrations dialer_settings 2>&1
python manage.py makemigrations dialer_campaign 2>&1
python manage.py makemigrations dialer_cdr 2>&1
python manage.py makemigrations dnc 2>&1
python manage.py makemigrations audiofield 2>&1
python manage.py makemigrations survey 2>&1
python manage.py makemigrations mod_sms 2>&1
python manage.py makemigrations callcenter 2>&1

echo ""
echo "=== All migrations created ==="
