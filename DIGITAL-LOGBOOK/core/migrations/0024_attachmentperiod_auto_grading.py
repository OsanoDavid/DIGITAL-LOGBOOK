from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('core', '0023_attachmentperiod_week_finalized_flags')]
    operations = [
        migrations.AddField(model_name='attachmentperiod', name='report_auto_score', field=models.FloatField(blank=True, null=True)),
        migrations.AddField(model_name='attachmentperiod', name='report_auto_feedback', field=models.JSONField(blank=True, default=dict)),
    ]
