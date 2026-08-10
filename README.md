# DIGITAL-LOGBOOK

This project is configured for Render with Python 3.12 and PostgreSQL.

For an existing Render web service, set `DATABASE_URL` to the database's **Internal Database URL** (or use Render's database connection-string environment-variable binding). Do not set it to the database name, such as `dhangongo`.

## Sending invitations from a Kisii University email address

For the currently configured Gmail sender (`odiwuorosano09@gmail.com`), create a Google App Password and add these environment variables to the Render web service. Do not commit or share the App Password.

```text
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=odiwuorosano09@gmail.com
EMAIL_HOST_PASSWORD=<Google App Password>
DEFAULT_FROM_EMAIL=Attachment Office <odiwuorosano09@gmail.com>
PUBLIC_SITE_URL=https://kisii-university-digital-logbook.onrender.com
```

After deployment, supervisor invitations are sent from `DEFAULT_FROM_EMAIL` and include a one-time password-setup link.
