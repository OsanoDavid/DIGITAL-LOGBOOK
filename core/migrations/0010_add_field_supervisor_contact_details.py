from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_add_field_supervisor_contact'),
    ]

    operations = [
        migrations.AddField(
            model_name='attachmentperiod',
            name='field_supervisor_phone',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='attachmentperiod',
            name='field_supervisor_id',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='attachmentperiod',
            name='field_supervisor_gender',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='attachmentperiod',
            name='field_supervisor_organization',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
