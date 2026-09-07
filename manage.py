#!/usr/bin/env python
import os
import sys

def main():
    # ============================================
    # CARGAR .env SOLO EN DESARROLLO LOCAL
    # ============================================
    # Intentar cargar dotenv, si no está instalado, ignorar
    try:
        from dotenv import load_dotenv
        # Cargar .env solo si el archivo existe
        if os.path.exists('.env'):
            load_dotenv()
            print("✅ Archivo .env cargado (desarrollo local)")
    except ImportError:
        # Si no está instalado python-dotenv, ignorar (Railway no lo necesita)
        pass
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'arteydis.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django..."
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()