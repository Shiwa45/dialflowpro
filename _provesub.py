import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.development'
django.setup()
from django_tenants.utils import schema_context
with schema_context('test_tenant'):
    from apps.dialer_campaign.models import Campaign, Subscriber
    from apps.dialer_campaign.tasks import collect_subscriber
    c = Campaign.objects.get(id=4)
    print(f"BEFORE: c#4 '{c.name}' subscribers={Subscriber.objects.filter(campaign=c).count()} allow_dup={c.allow_duplicate_contacts}")
    # enable the new flag and re-collect
    c.allow_duplicate_contacts = True
    c.save(update_fields=['allow_duplicate_contacts'])
    collect_subscriber(4, 'test_tenant')
    c.refresh_from_db()
    print(f"AFTER allow_dup=True + collect: subscribers={Subscriber.objects.filter(campaign=c).count()} totalcontact={c.totalcontact}")
    # idempotency: run again, should not double
    collect_subscriber(4, 'test_tenant')
    print(f"AFTER 2nd collect (idempotency): subscribers={Subscriber.objects.filter(campaign=c).count()}")
