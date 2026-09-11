import os, sys

def verify(path, username, password):
    print('--- Verifying project at', path)
    sys.path.insert(0, path)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sist_project.settings')
    try:
        import django
        django.setup()
        from django.contrib.auth import get_user_model
        User = get_user_model()
        u = User.objects.filter(username__iexact=username).first()
        if not u:
            print('No user found')
            return
        print('password field:', u.password[:60])
        print('check_password:', u.check_password(password))
    except Exception as e:
        print('Error:', e)
    finally:
        try:
            sys.path.remove(path)
        except Exception:
            pass

if __name__ == '__main__':
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for p in (base, os.path.join(base, 'DIGITAL-LOGBOOK')):
        verify(p, 'admin', os.environ.get('NEW_ADMIN_PASSWORD', 'KisiiAdmin!2026'))
