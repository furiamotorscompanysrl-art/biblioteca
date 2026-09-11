# gunicorn.conf.py
import os

# Puerto
bind = f"0.0.0.0:{os.environ.get('PORT', '8080')}"

# Workers
workers = int(os.environ.get('GUNICORN_WORKERS', '2'))
worker_class = 'sync'

# ✅ TIMEOUT AUMENTADO A 10 MINUTOS (600 segundos)
timeout = int(os.environ.get('GUNICORN_TIMEOUT', '600'))

# Keepalive
keepalive = 5

# Requests
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# ✅ Permitir archivos grandes
limit_request_line = 0
limit_request_field_size = 0