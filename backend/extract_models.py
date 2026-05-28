import django
import json
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from django.apps import apps

data = {}
for m in apps.get_models():
    if m.__module__.startswith('apps.'):
        data[m.__name__] = [f.name for f in m._meta.fields]

print(json.dumps(data, indent=2))
