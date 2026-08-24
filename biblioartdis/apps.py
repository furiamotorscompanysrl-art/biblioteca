# apps.py - CORREGIDO
from django.apps import AppConfig
import os

class BiblioartdisConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'biblioartdis'
    path = os.path.dirname(os.path.abspath(__file__))
    
    def ready(self):
        # Solo importar señales si el archivo existe
        try:
            import biblioartdis.signals
        except ImportError:
            pass  # No hay archivo signals.py, no pasa nada