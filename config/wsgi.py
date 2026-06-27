"""
WSGI config for config project.
"""

import os
import subprocess
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# ── تشغيل collectstatic تلقائياً عند كل deploy ──
subprocess.run(
    ['python', 'manage.py', 'collectstatic', '--noinput'],
    check=False
)

application = get_wsgi_application()
