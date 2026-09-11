import os
import sys

def set_password_for_project(path, username, password):
    print('--- Setting admin in', path)
    sys.path.insert(0, path)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sist_project.settings')
    try:
        import django
        django.setup()
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.filter(username__iexact=username).first()
        if not user:
            print('User not found in', path)
            return False
        user.set_password(password)
        user.is_superuser = True
        user.is_staff = True
        if getattr(user, 'role', '') != 'ADMIN':
            user.role = 'ADMIN'
        user.save()
        print('Password set and admin flags ensured for', user.username)
        return True
    except Exception as e:
        print('Error:', e)
        return False
    finally:
        try:
            sys.path.remove(path)
        except Exception:
            pass

if __name__ == '__main__':
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    username = os.environ.get('RESET_ADMIN_USERNAME', 'admin')
    password = os.environ.get('NEW_ADMIN_PASSWORD', 'KisiiAdmin!2026')
    ok1 = set_password_for_project(base, username, password)
    ok2 = set_password_for_project(os.path.join(base, 'DIGITAL-LOGBOOK'), username, password)
    if ok1 and ok2:
        print('\nAll done. Admin password updated in both projects.')
        print('Username:', username)
        print('Password:', password)
    else:
        print('\nSome updates failed. See messages above.')
