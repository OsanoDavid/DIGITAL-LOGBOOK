import os
import sys

def try_auth(path, username, password):
    print('--- Trying project at', path)
    sys.path.insert(0, path)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sist_project.settings')
    try:
        import django
        django.setup()
        from django.contrib.auth import authenticate
        user = authenticate(username=username, password=password)
        print('Authenticated:', bool(user), 'User:', getattr(user, 'username', None), 'Role:', getattr(user, 'role', None) if user else None)
    except Exception as e:
        print('Error during auth:', e)
    finally:
        try:
            sys.path.remove(path)
        except Exception:
            pass

if __name__ == '__main__':
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for p in (base, os.path.join(base, 'DIGITAL-LOGBOOK')):
        try_auth(p, 'admin', os.environ.get('RESET_ADMIN_PASSWORD', 'ChangeMe123!'))
