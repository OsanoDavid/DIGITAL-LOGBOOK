import os
import sys
import importlib

def check_project(path):
    print('--- Checking project at', path)
    if not os.path.isdir(path):
        print('Path missing')
        return
    sys.path.insert(0, path)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sist_project.settings')
    try:
        import django
        django.setup()
        from core.models import User
        admins = User.objects.filter(role='ADMIN')
        superadmins = User.objects.filter(is_superuser=True)
        print('Admins (role=ADMIN):', [u.username for u in admins])
        print('Superusers (is_superuser):', [u.username for u in superadmins])
    except Exception as e:
        print('Error importing Django or querying users:', e)
    finally:
        # clean up path
        try:
            sys.path.remove(path)
        except Exception:
            pass

if __name__ == '__main__':
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    check_project(base)  # root project
    check_project(os.path.join(base, 'DIGITAL-LOGBOOK'))
