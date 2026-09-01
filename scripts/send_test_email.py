import os
import sys
import traceback
from pathlib import Path

# Ensure project root is on sys.path so we can import the Django project package
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sist_project.settings')

try:
    import django
    django.setup()
    from django.conf import settings
except Exception:
    print('Failed to set up Django:')
    traceback.print_exc()
    sys.exit(1)

import smtplib
from email.message import EmailMessage

EMAIL_HOST = os.environ.get('EMAIL_HOST', getattr(settings, 'EMAIL_HOST', 'smtp.gmail.com'))
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', getattr(settings, 'EMAIL_PORT', 587)))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', str(getattr(settings, 'EMAIL_USE_TLS', True))).lower() in {'true', '1', 'yes'}
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', getattr(settings, 'EMAIL_HOST_USER', ''))
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', getattr(settings, 'EMAIL_HOST_PASSWORD', ''))
TEST_TO = os.environ.get('EMAIL_TEST_TO', EMAIL_HOST_USER or 'test@example.com')

print('SMTP host:', EMAIL_HOST, 'port:', EMAIL_PORT, 'use_tls:', EMAIL_USE_TLS)
print('User:', EMAIL_HOST_USER)
print('Password provided:', bool(EMAIL_HOST_PASSWORD))
print('Test recipient:', TEST_TO)

msg = EmailMessage()
msg['Subject'] = 'DIGITAL-LOGBOOK test email'
msg['From'] = EMAIL_HOST_USER or 'test@example.com'
msg['To'] = TEST_TO
msg.set_content('This is a test email from DIGITAL-LOGBOOK send_test_email.py')

try:
    # Prefer Django's send_mail (Anymail API backend) first — it uses the
    # configured EMAIL_BACKEND in settings (e.g. anymail Mailgun API).
    try:
        from django.core.mail import send_mail
        print('\nTrying Django send_mail() (Anymail/API backend)...')
        result = send_mail('DIGITAL-LOGBOOK Django test', 'Body from Django send_mail', msg['From'], [TEST_TO], fail_silently=False)
        print('send_mail result:', result)
        print('Django send_mail succeeded')
    except Exception:
        print('\nDjango send_mail failed; falling back to raw SMTP:')
        traceback.print_exc()
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=20) as smtp:
            smtp.set_debuglevel(1)
            smtp.ehlo()
            if EMAIL_USE_TLS:
                smtp.starttls()
                smtp.ehlo()
            if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
                print('Attempting SMTP login...')
                smtp.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
                print('Login succeeded')
            else:
                print('Skipping login because credentials are missing')

            print('Attempting to send test email via SMTP...')
            smtp.send_message(msg)
            print('SMTP send_message completed without exception')

except Exception:
    print('SMTP test failed with exception:')
    traceback.print_exc()
    sys.exit(2)

# Also try Django's send_mail to surface Django-related errors
try:
    from django.core.mail import send_mail
    print('\nTrying Django send_mail()...')
    result = send_mail('DIGITAL-LOGBOOK Django test', 'Body from Django send_mail', msg['From'], [TEST_TO], fail_silently=False)
    print('send_mail result:', result)
except Exception:
    print('Django send_mail failed:')
    traceback.print_exc()
    sys.exit(3)

print('\nTest completed successfully')
