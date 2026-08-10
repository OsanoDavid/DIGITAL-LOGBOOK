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

## Quick: Seed Attachment Administrator (fast)

If you want a ready `ATTACHMENT_ADMIN` account quickly, add these environment secrets to your Render service and redeploy:

```
ATTACHMENT_ADMIN_USERNAME=attachmentadmin
ATTACHMENT_ADMIN_EMAIL=attachmentadmin@example.com
ATTACHMENT_ADMIN_PASSWORD=Attachment@2026
```

After deploy, run migrations (if not automatic) and verify the user exists:

```bash
python manage.py migrate --noinput

To skip running migrations during deployment (useful when you don't want pushes to modify the production database), set the environment variable `RUN_MIGRATIONS=0` in your deployment environment. Example (Render): set `RUN_MIGRATIONS` to `0` in your service's Environment > ENV VARS settings. The `render.yaml` and `start.sh` scripts respect this variable.

Safety note: the startup script now checks whether any migrations have already been applied. If `RUN_MIGRATIONS=0` and the database contains no applied migrations, the service will abort startup to avoid running the app against an uninitialized DB. To intentionally skip migrations on a fresh DB, either set `RUN_MIGRATIONS=1` or initialize the database first (run `python manage.py migrate`).

Render checklist for persistent DB:

- Ensure your Render service has a persistent disk mount (size >= 1GB) and that `SQLITE_DB_PATH` is set to the mounted file path (e.g. `/data/db.sqlite3`).
- Set `USE_SQLITE=true` and `SQLITE_DB_PATH=/data/db.sqlite3` in the service ENV VARS if you want SQLite on Render.
- For typical Postgres on Render, set `DATABASE_URL` and leave `USE_SQLITE` unset or `false`.
- If your production DB keeps resetting, check that:
	- The service `startCommand` uses `bash start.sh` (it does in `render.yaml`).
	- `RUN_MIGRATIONS` is not accidentally set to `0` on first-time deploys.
	- The persistent disk mount is configured and writable by the service user.

When you redeploy, the `start.sh` script prints the resolved DB path and applied migration count; paste that output here if the problem continues.
python manage.py collectstatic --noinput
python manage.py shell -c "from core.models import User; print(User.objects.filter(username='attachmentadmin').exists())"
```

Login with `attachmentadmin` / `Attachment@2026` at your admin-login URL. Do NOT commit or share these credentials; use Render Secrets for production.

