import os
import sys
import django

# Ensure project root on path
proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sist_project.settings')
import importlib
from django.conf import settings

# Force in-memory email backend for this run
settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

django.setup()

from django.urls import reverse
from django.test import Client
from core.models import User, LecturerProfile
from django.core import mail

print('\n=== E2E Admin Create Lecturer Test ===\n')

# Create or get admin user
admin_username = 'admin_test'
admin_email = 'admin_test@example.com'
admin_password = 'AdminPass!23'
User.objects.filter(username=admin_username).delete()
admin_user = User.objects.create_user(username=admin_username, email=admin_email, password=admin_password)
admin_user.role = 'ADMIN'
admin_user.is_staff = True
admin_user.is_superuser = False
admin_user.save()

client = Client()
client.force_login(admin_user)

# Prepare lecturer data
lec_email = 'created_lecturer@example.com'
User.objects.filter(email=lec_email).delete()
post_data = {
    'role': 'LECTURER',
    'username': '',  # blank to test fallback to email
    'email': lec_email,
    'full_name': 'Created Lecturer',
    'phone_number': '+254700000000',
    'institution_or_company': 'Kisii University',
    'course': 'Computer Science',
    # Lecturer profile required fields
    'workspace_role': 'Senior Lecturer',
    'national_id': '12345678',
    'specialization': 'Computer Science',
    'faculty': 'SIST',
    'department': 'Computer Science',
}

create_url = reverse('core:admin_create_user')
resp = client.post(create_url, post_data, follow=True)
print('POST to admin_create_user status_code:', resp.status_code)

# Check created user in DB
try:
    created = User.objects.get(email=lec_email)
    print('Created user id:', created.id)
    print('username:', created.username)
    print('role:', created.role)
    print('must_change_password:', created.must_change_password)
except User.DoesNotExist:
    print('User not created.')
    raise SystemExit(1)

# Check lecturer profile
try:
    profile = LecturerProfile.objects.get(user=created)
    print('Lecturer profile created: university:', profile.university, 'department:', profile.department)
except LecturerProfile.DoesNotExist:
    print('Lecturer profile not created.')

# Inspect in-memory email outbox
if mail.outbox:
    print('\nCaptured email count:', len(mail.outbox))
    last = mail.outbox[-1]
    print('Email subject:', last.subject)
    print('Email to:', last.to)
    print('Email body snippet:', last.body[:400])
else:
    print('\nNo emails captured in locmem outbox.')

print('\n=== Test complete ===\n')
