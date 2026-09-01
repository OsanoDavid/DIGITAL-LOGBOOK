from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_seed_attachment_admin'),
    ]

    operations = [
        migrations.CreateModel(
            name='LecturerProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('workspace_role', models.CharField(blank=True, max_length=120)),
                ('national_id', models.CharField(blank=True, max_length=50)),
                ('specialization', models.CharField(blank=True, max_length=120)),
                ('university', models.CharField(blank=True, max_length=255)),
                ('faculty', models.CharField(blank=True, max_length=255)),
                ('department', models.CharField(blank=True, max_length=255)),
                ('university_email', models.EmailField(blank=True, max_length=254)),
                ('user', models.OneToOneField(on_delete=models.deletion.CASCADE, related_name='lecturer_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
