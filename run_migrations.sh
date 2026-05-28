#!/bin/bash
set -e

VENV=/opt/dialflow-venv
PROJECT=/mnt/c/Users/easyian/dialflow/backend

source $VENV/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.development
cd $PROJECT

echo "=== Running shared schema migrations (public) ==="
python manage.py migrate_schemas --shared 2>&1

echo ""
echo "=== Running all migrations ==="
python manage.py migrate 2>&1

echo ""
echo "=== Migrations complete ==="
