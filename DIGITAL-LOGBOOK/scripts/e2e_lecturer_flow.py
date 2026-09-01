import os
import sys
import django
import secrets

# Ensure project root is on sys.path so `sist_project` can be imported
proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sist_project.settings')
django.setup()


from django.urls import reverse
from django.test import Client
from core.models import User, LecturerProfile, SystemSettings

print('\n=== E2E Lecturer Create & Forced-Password-Change Test ===\n')

# Ensure unique username
username = 'lec_test_user'
email = 'lec_test_user@example.com'
new_password = 'NewSecurePass!23'

# Remove if exists
User.objects.filter(username=username).delete()

# Generate temporary password
temp_password = secrets.token_urlsafe(10)

# Create user
user = User.objects.create_user(username=username, email=email, password=temp_password)
user.first_name = 'Temp'
user.last_name = 'Lecturer'
user.role = 'LECTURER'
user.must_change_password = True
user.save()

# Create lecturer profile
LecturerProfile.objects.filter(user=user).delete()
LecturerProfile.objects.create(user=user, university='Kisii University')

print('Created user:')
print(' - id:', user.id)
print(' - username:', user.username)
print(' - email:', user.email)
print(' - role:', user.role)
print(' - must_change_password:', user.must_change_password)
print(' - temp password (DELIVERED IN CONSOLE):', temp_password)

# Start test client
client = Client()

login_url = reverse('core:login')
print('\nPosting to login view...')
resp = client.post(login_url, {'username': username, 'password': temp_password, 'role': 'LECTURER'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
print('Login HTTP status:', resp.status_code)
try:
    print('Login JSON:', resp.json())
    redirect_url = resp.json().get('redirect_url')
except Exception:
    redirect_url = resp.get('Location')
    print('Login response not JSON; Location:', redirect_url)

if not redirect_url:
    print('Did not receive redirect URL — login likely failed.')
    raise SystemExit(1)

print('Expected redirect to:', redirect_url)

# Simulate visiting change password page and posting new password
if 'change_initial_password' in redirect_url or redirect_url.endswith(reverse('core:change_initial_password')):
    change_url = reverse('core:change_initial_password')
    print('\nPosting new password to change-initial-password view...')
    resp2 = client.post(change_url, {'password': new_password, 'confirm_password': new_password})
    print('Change password status code:', resp2.status_code)
    # Refresh user
    user.refresh_from_db()
    print('After password change, must_change_password:', user.must_change_password)
    # Verify new login works
    client.logout()
    logged_in = client.login(username=username, password=new_password)
    print('Client.login with new password:', logged_in)
else:
    print('Redirect does not point to change-password. Received:', redirect_url)

print('\n=== Test complete ===\n')
