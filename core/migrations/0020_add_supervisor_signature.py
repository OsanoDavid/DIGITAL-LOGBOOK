from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_attachmentperiod_week_12_finalized_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='weeklylog',
            name='supervisor_signature',
            field=models.ImageField(upload_to='signatures/', null=True, blank=True),
        ),
    ]
