import os
import shutil
import time
import subprocess

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE, 'db.sqlite3')
BACKUPS_DIR = os.path.join(BASE, 'backups')
MEDIA_DIRS = [os.path.join(BASE, 'media'), os.path.join(BASE, 'static_media'), os.path.join(BASE, 'DIGITAL-LOGBOOK', 'media')]

os.makedirs(BACKUPS_DIR, exist_ok=True)

timestamp = time.strftime('%Y%m%d%H%M%S')
if os.path.exists(DB_PATH):
    dst = os.path.join(BACKUPS_DIR, f'db_backup_{timestamp}.sqlite3')
    shutil.copy2(DB_PATH, dst)
    print('DB backed up to', dst)
else:
    print('No DB file found at', DB_PATH)

# Run manage.py flush to clear all data (keeps schema)
try:
    print('Running manage.py flush --no-input')
    subprocess.run([os.path.join(BASE, '.venv', 'Scripts', 'python.exe'), os.path.join(BASE, 'manage.py'), 'flush', '--no-input'], check=True)
    print('Database flushed')
except Exception as e:
    print('Failed to run flush:', e)

# Remove media directories and their contents
for d in MEDIA_DIRS:
    # normalize path if overly nested
    if d.endswith(os.path.join('DIGITAL-LOGBOOK', 'media')):
        d = os.path.join(BASE, 'media')
    if os.path.exists(d):
        try:
            shutil.rmtree(d)
            print('Removed media directory', d)
        except Exception as e:
            print('Failed to remove', d, e)
    else:
        print('No media directory at', d)

print('Clear operation completed. Backup is preserved in backups/.')
