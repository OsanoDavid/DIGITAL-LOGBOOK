#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess
import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(ROOT)
os.chdir(PROJECT_ROOT)
# Ensure project root is on sys.path so imports like `sist_project` work
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def main():
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    db_path = os.path.join(PROJECT_ROOT, 'db.sqlite3')
    backup_dir = os.path.join(PROJECT_ROOT, 'backups')
    os.makedirs(backup_dir, exist_ok=True)

    if os.path.exists(db_path):
        backup_path = os.path.join(backup_dir, f'db_backup_{timestamp}.sqlite3')
        shutil.copy2(db_path, backup_path)
        print('Backed up database to', backup_path)
        try:
            os.remove(db_path)
            print('Removed', db_path)
        except Exception as e:
            print('Failed to remove db.sqlite3:', e)
            sys.exit(1)
    else:
        print('No db.sqlite3 found; skipping removal')

    # Run migrations
    print('Running migrations...')
    subprocess.check_call([sys.executable, 'manage.py', 'migrate'])
    print('Migrations applied')

    # Create superuser
    print('Ensuring superuser exists...')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sist_project.settings')
    import django
    django.setup()
    from django.contrib.auth import get_user_model
    User = get_user_model()

    username = os.environ.get('RESET_ADMIN_USERNAME', 'admin')
    email = os.environ.get('RESET_ADMIN_EMAIL', 'admin@example.com')
    password = os.environ.get('RESET_ADMIN_PASSWORD', 'ChangeMe123!')

    existing = User.objects.filter(username__iexact=username).first()
    if not existing:
        user = User.objects.create_superuser(username=username, email=email, password=password)
        # Ensure role and staff flags are set for the admin console
        user.role = 'ADMIN'
        user.is_staff = True
        user.is_superuser = True
        user.save()
        print('Created superuser:', username)
    else:
        # Ensure existing user has admin privileges and role
        updated = False
        if not existing.is_superuser:
            existing.is_superuser = True
            updated = True
        if not existing.is_staff:
            existing.is_staff = True
            updated = True
        if getattr(existing, 'role', '') != 'ADMIN':
            existing.role = 'ADMIN'
            updated = True
        # Optionally reset password if env var was provided
        if password and not existing.check_password(password):
            existing.set_password(password)
            updated = True
        if updated:
            existing.save()
            print('Updated existing user to admin:', username)
        else:
            print('Superuser already exists and is up-to-date:', username)

    # Run sanity check
    print('Running Django system check...')
    subprocess.check_call([sys.executable, 'manage.py', 'check'])
    print('System check passed')

if __name__ == '__main__':
    main()
