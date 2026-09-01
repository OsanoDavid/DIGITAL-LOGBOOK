from django.db import migrations
import os


def create_admin(apps, schema_editor):
    User = apps.get_model('core', 'User')

    if User.objects.filter(role='ADMIN').exists():
        return

    username = os.environ.get('ADMIN_USERNAME', 'superadmin').strip()
    email = os.environ.get('ADMIN_EMAIL', 'superadmin@example.com').strip()
    password = os.environ.get('ADMIN_PASSWORD', '').strip()

    if not password:
        # Do not create a default admin without an explicit password.
        return

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        role='ADMIN',
        is_staff=True,
        is_superuser=True,
    )
    user.save()


def noop_reverse(apps, schema_editor):
    # Do not delete admin users on reverse migration.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_alter_user_profile_photo'),
    ]

    operations = [
        migrations.RunPython(create_admin, noop_reverse),
    ]
