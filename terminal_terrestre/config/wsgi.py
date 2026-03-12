"""
Terminal Terrestre — WSGI Application
Punto de entrada para servidores WSGI (Waitress en producción Windows).
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()
