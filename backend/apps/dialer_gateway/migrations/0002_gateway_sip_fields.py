from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dialer_gateway', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='gateway',
            name='sip_host',
            field=models.CharField(
                blank=True, max_length=255,
                verbose_name='SIP host',
                help_text='IP or hostname of the SIP/GSM gateway (e.g. 192.168.1.113)'
            ),
        ),
        migrations.AddField(
            model_name='gateway',
            name='sip_port',
            field=models.PositiveIntegerField(default=5060, verbose_name='SIP port'),
        ),
        migrations.AddField(
            model_name='gateway',
            name='register',
            field=models.BooleanField(
                default=False, verbose_name='register',
                help_text='Whether FreeSWITCH should register with this gateway'
            ),
        ),
        migrations.AddField(
            model_name='gateway',
            name='sip_username',
            field=models.CharField(blank=True, max_length=255, verbose_name='SIP username'),
        ),
        migrations.AddField(
            model_name='gateway',
            name='sip_password',
            field=models.CharField(blank=True, max_length=255, verbose_name='SIP password'),
        ),
        migrations.AddField(
            model_name='gateway',
            name='caller_id_in_from',
            field=models.BooleanField(
                default=True, verbose_name='caller ID in From header',
                help_text='Pass caller ID via SIP From header (recommended for GSM gateways)'
            ),
        ),
    ]
