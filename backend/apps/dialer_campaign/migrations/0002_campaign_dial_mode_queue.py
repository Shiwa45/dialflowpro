from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('callcenter', '0002_agent_sip_credentials'),
        ('dialer_campaign', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='campaign',
            name='dial_mode',
            field=models.IntegerField(
                choices=[(1, 'Predictive'), (2, 'Preview'), (3, 'Progressive'), (4, 'Manual')],
                default=1,
                help_text='Predictive: auto-dial & route; Preview: agent reviews first; Progressive: 1:1 ratio; Manual: agent dials',
                verbose_name='dial mode',
            ),
        ),
        migrations.AddField(
            model_name='campaign',
            name='queue',
            field=models.ForeignKey(
                blank=True,
                help_text='Queue that receives answered calls from this campaign',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='campaigns',
                to='callcenter.queue',
                verbose_name='queue',
            ),
        ),
    ]
