"""
Provision (or update) a tenant's AI agent subscription.

Subscriptions are server-side only — a tenant admin can't grant themselves AI
access through the API. Use this command (or your billing webhook) to flip it on.

    python manage.py provision_ai_subscription --schema acme \
        --plan standard --max-agents 3 --minutes 5000 --active
"""
from datetime import date, timedelta

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create or update a tenant's AI subscription."

    def add_arguments(self, parser):
        parser.add_argument("--schema", required=True, help="Tenant schema_name")
        parser.add_argument("--plan", default="standard")
        parser.add_argument("--max-agents", type=int, default=1)
        parser.add_argument("--minutes", type=int, default=1000)
        parser.add_argument("--active", action="store_true")
        parser.add_argument("--deactivate", action="store_true")

    def handle(self, *args, **o):
        from django_tenants.utils import schema_context, get_tenant_model
        from apps.ai_agent.models import AISubscription

        TenantModel = get_tenant_model()
        try:
            tenant = TenantModel.objects.get(schema_name=o["schema"])
        except TenantModel.DoesNotExist:
            raise CommandError(f"No tenant with schema '{o['schema']}'")

        with schema_context(o["schema"]):
            sub, created = AISubscription.objects.get_or_create(tenant=tenant)
            sub.plan_name = o["plan"]
            sub.max_agents = o["max_agents"]
            sub.monthly_minute_quota = o["minutes"]
            if o["active"]:
                sub.is_active = True
            if o["deactivate"]:
                sub.is_active = False
            if not sub.period_start:
                sub.period_start = date.today()
                sub.period_end = date.today() + timedelta(days=30)
            sub.save()

        state = "created" if created else "updated"
        self.stdout.write(self.style.SUCCESS(
            f"AI subscription {state} for '{o['schema']}': "
            f"active={sub.is_active}, max_agents={sub.max_agents}, "
            f"minutes={sub.monthly_minute_quota}"
        ))
