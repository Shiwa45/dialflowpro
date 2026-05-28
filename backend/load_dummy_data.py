import os
import django
from django.utils import timezone
from datetime import timedelta
import random

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from django_tenants.utils import tenant_context
from apps.tenants.models import Tenant, Domain
from apps.accounts.models import User, UserProfile, UserRole
from apps.dialer_settings.models import DialerSetting
from apps.dialer_gateway.models import Gateway
from apps.dialer_contact.models import Phonebook, Contact
from apps.dialer_campaign.models import Campaign
from apps.dnc.models import DNC, DNCContact
from apps.survey.models import Survey, SurveySection
from apps.mod_sms.models import SmsGateway, SmsCampaign
from apps.callcenter.models import Queue, Agent, Tier

def create_dummy_data():
    print("=== Starting Dummy Data Generation ===")

    # 1. Create Tenant (Shared Schema)
    tenant_name = 'test_tenant'
    tenant, created = Tenant.objects.get_or_create(
        schema_name=tenant_name,
        defaults={'name': 'Test Organization', 'is_active': True, 'plan': 'pro'}
    )
    if created:
        print(f"Created tenant: {tenant.name} ({tenant.schema_name})")
        # Run migrations for the new tenant
        django.core.management.call_command('migrate_schemas', tenant=True, schema_name=tenant_name, interactive=False)
    else:
        print(f"Tenant already exists: {tenant.name}")

    domain, d_created = Domain.objects.get_or_create(
        domain='test.localhost',
        defaults={'tenant': tenant, 'is_primary': True}
    )
    if d_created:
        print(f"Created domain: {domain.domain}")

    # 2. Create Dialer Settings & Users (Shared Schema)
    setting, s_created = DialerSetting.objects.get_or_create(
        name='Default Limits',
        tenant=tenant,
        defaults={
            'max_frequency': 100,
            'callmaxduration': 3600,
            'maxretry': 3,
            'max_cpg': 10,
            'sms_max_frequency': 50
        }
    )

    manager, m_created = User.objects.get_or_create(
        username='manager@test.local',
        defaults={
            'email': 'manager@test.local',
            'role': UserRole.MANAGER,
            'tenant': tenant,
            'is_active': True,
            'is_staff': True
        }
    )
    if m_created:
        manager.set_password('Pass@123')
        manager.save()
        UserProfile.objects.create(user=manager, dialersetting=setting)
        print("Created Manager user: manager@test.local / Pass@123")

    agent, a_created = User.objects.get_or_create(
        username='agent@test.local',
        defaults={
            'email': 'agent@test.local',
            'role': UserRole.AGENT,
            'tenant': tenant,
            'is_active': True
        }
    )
    if a_created:
        agent.set_password('Pass@123')
        agent.save()
        UserProfile.objects.create(user=agent, dialersetting=setting)
        print("Created Agent user: agent@test.local / Pass@123")

    # 3. Create Operational Data (Tenant Schema)
    print("\n--- Switching to tenant schema to create app data ---")
    with tenant_context(tenant):
        # Gateway
        gateway, gw_created = Gateway.objects.get_or_create(
            name='Twilio SIP Trunk',
            defaults={
                'status': 1, # Active
                'gateways': 'sofia/gateway/twilio/',
                'maximum_call': 100
            }
        )
        if gw_created: print("Created Gateway")

        # Phonebook & Contacts
        phonebook, pb_created = Phonebook.objects.get_or_create(
            name='Test Leads Q3',
            user=manager,
            defaults={'description': 'A list of generated test leads.'}
        )
        if pb_created:
            print("Created Phonebook. Adding 50 dummy contacts...")
            contacts_to_create = []
            for i in range(1, 51):
                contacts_to_create.append(
                    Contact(
                        phonebook=phonebook,
                        contact=f"+1555000{i:04d}",
                        first_name=f"Lead{i}",
                        last_name="Test",
                        email=f"lead{i}@example.com",
                        status=1 # Active
                    )
                )
            Contact.objects.bulk_create(contacts_to_create)

        # DNC List
        dnc_list, dnc_created = DNC.objects.get_or_create(
            name='Global DNC',
            user=manager,
            defaults={'description': 'Do Not Call numbers'}
        )
        if dnc_created:
            DNCContact.objects.create(dnc=dnc_list, phone_number='+15550009999')
            print("Created DNC list")

        # Survey
        survey, sv_created = Survey.objects.get_or_create(
            name='Customer Satisfaction',
            user=manager,
            defaults={'status': 1}
        )
        if sv_created:
            SurveySection.objects.create(
                survey=survey,
                section_type=1, # PLAY_MESSAGE
                name='Intro',
                order=1,
            )
            print("Created Survey")

        # Call Center Queue & Agent
        queue, q_created = Queue.objects.get_or_create(
            name='Sales Support',
            user=manager,
            defaults={'strategy': 1}
        )
        if q_created: print("Created Call Center Queue")

        cc_agent, cca_created = Agent.objects.get_or_create(
            name='Support Agent 1',
            user=manager,
            defaults={'contact': '[leg_timeout=10]user/1000'}
        )
        if cca_created:
            Tier.objects.create(queue=queue, agent=cc_agent, level=1, position=1)
            print("Created Call Center Agent & Tier")

        # Campaign
        campaign, c_created = Campaign.objects.get_or_create(
            name='Outbound Sales Q3',
            user=manager,
            defaults={
                'campaign_code': 'SALES_Q3',
                'status': 1, # Active
                'callerid': '+18005551234',
                'startingdate': timezone.now(),
                'expirationdate': timezone.now() + timedelta(days=30),
                'frequency': 10,
                'callmaxduration': 300,
                'dnc_list': dnc_list,
                'aleg_gateway': gateway
            }
        )
        if c_created:
            # We must assign the phonebook via many-to-many? No, Campaign uses imported_phonebook foreign key
            campaign.imported_phonebook = str(phonebook.id)
            campaign.save()
            print("Created Campaign")

        # SMS Gateway & Campaign
        sms_gw, sgw_created = SmsGateway.objects.get_or_create(
            name='Twilio SMS',
            user=manager,
            defaults={
                'gateway_type': 1,
                'account_sid': 'ACdummy',
                'auth_token': 'dummy',
                'from_number': '+18005559999'
            }
        )
        if sgw_created:
            SmsCampaign.objects.create(
                name='Promo Blast',
                user=manager,
                gateway=sms_gw,
                message_text='Hello {{first_name}}, check out our new promo!',
                startingdate=timezone.now(),
                expirationdate=timezone.now() + timedelta(days=30),
                frequency=5
            )
            print("Created SMS Gateway & Campaign")

    print("\n=== Dummy Data Generation Complete ===")

if __name__ == '__main__':
    create_dummy_data()
