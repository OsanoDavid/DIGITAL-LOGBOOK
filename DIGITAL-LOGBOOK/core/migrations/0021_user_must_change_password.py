from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_systemsettings_landing_stats'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='must_change_password',
            field=models.BooleanField(default=False),
        ),
    ]
