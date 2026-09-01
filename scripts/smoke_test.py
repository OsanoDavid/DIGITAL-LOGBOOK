from django.contrib.auth import get_user_model
from core.models import AttachmentPeriod, WeeklyLog
from django.test import Client

User = get_user_model()

u, created = User.objects.get_or_create(username='smoke_student')
if created:
    u.role = 'STUDENT'
    u.set_password('testpass')
    u.save()
    print('Created user smoke_student')
else:
    print('User exists:', u.username)

c = Client()

# Attempt login
resp = c.post('/', {'username': 'smoke_student', 'password': 'testpass'})
print('LOGIN -> status:', resp.status_code)
try:
    print('LOGIN content:', resp.content.decode())
except Exception:
    print(resp.content)

# Ensure period exists
period, _ = AttachmentPeriod.objects.get_or_create(student=u, defaults={'start_date': '2026-01-01'})
print('Period id:', period.id)

# Call create_log endpoint (not following redirects)
url = f'/portal/log/create/{period.id}/'
resp2 = c.get(url, follow=False)
print('CREATE_LOG (no-follow) status:', resp2.status_code)
print('Location header:', resp2.get('Location'))

# Call create_log endpoint and follow redirects
resp3 = c.get(url, follow=True)
print('CREATE_LOG (follow) final path:', resp3.request.get('PATH_INFO'))
print('FINAL status:', resp3.status_code)

# Show first 3 weekly logs
logs = period.weekly_logs.all().order_by('week_number')[:3]
for w in logs:
    print('Week', w.week_number, 'id', w.id, 'monday_activity set?', bool(w.monday_activity))
