# asgi.py
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'arteydis.settings')  # Cambiar a arteydis

application = get_asgi_application()