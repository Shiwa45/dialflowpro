#!/bin/bash
set -e

VENV=/opt/dialflow-venv
PROJECT=/mnt/c/Users/easyian/dialflow/backend

source $VENV/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.development

echo "=== Testing DB Connection ==="
cd $PROJECT
python -c "
import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.development'
django.setup()
from django.db import connection
connection.ensure_connection()
print('DB connected OK:', connection.vendor)
"
