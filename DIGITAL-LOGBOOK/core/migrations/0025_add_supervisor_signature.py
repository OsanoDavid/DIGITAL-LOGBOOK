from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0024_attachmentperiod_auto_grading'),
    ]

    operations = [
        migrations.AddField(
            model_name='weeklylog',
            name='supervisor_signature',
            field=models.ImageField(upload_to='signatures/', null=True, blank=True),
        ),
    ]
