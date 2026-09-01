import os
import sys

sys.path.append(r"C:\Users\Admin\Desktop\kisii1\DIGITAL-LOGBOOK")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sist_project.settings")

import django

django.setup()

from core.models import User
from django.test import Client

u = User.objects.filter(username="superadmin").first()
created = False
if u is None:
    u = User(username="superadmin", email="superadmin@example.com", role="ADMIN", is_staff=True, is_superuser=True)
    u.set_password("SuperAdmin123!")
    u.save()
    created = True
else:
    u.set_password("SuperAdmin123!")
    u.save()

print("created", created, "username", u.username, "role", u.role, "is_staff", u.is_staff, "is_superuser", u.is_superuser)

c = Client()
response = c.post('/portal/admins/', {'username': 'superadmin', 'password': 'SuperAdmin123!'})
print('status_code', response.status_code)
print('redirect', response.url if response.has_header('Location') else None)
print('content_snippet', response.content[:200].decode('utf-8', errors='replace'))
