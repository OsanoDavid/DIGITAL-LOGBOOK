from django.db import migrations
import os


def create_attachment_admin(apps, schema_editor):
    User = apps.get_model('core', 'User')

    username = os.environ.get('ATTACHMENT_ADMIN_USERNAME', '').strip()
    email = os.environ.get('ATTACHMENT_ADMIN_EMAIL', '').strip()
    password = os.environ.get('ATTACHMENT_ADMIN_PASSWORD', '').strip()

    if not username or not password:
        # Do not create a default attachment admin without explicit username and password.
        return

    user, created = User.objects.get_or_create(username=username)
    if created:
        user.email = email or ''
        user.role = 'ATTACHMENT_ADMIN'
        user.is_staff = True
        user.set_password(password)
        user.first_name = 'Attachment'
        user.last_name = 'Administrator'
        user.save()
    else:
        # If user exists, ensure role and password are set (do not overwrite email if provided blank)
        updated = False
        if user.role != 'ATTACHMENT_ADMIN':
            user.role = 'ATTACHMENT_ADMIN'
            updated = True
        if password:
            user.set_password(password)
            updated = True
        if email and user.email != email:
            user.email = email
            updated = True
        if updated:
            user.save()


def noop_reverse(apps, schema_editor):
    # Do not delete seeded users on reverse migration.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_alter_adminnotification_id'),
    ]

    operations = [
        migrations.RunPython(create_attachment_admin, reverse_code=noop_reverse),
    ]
