# core/settings/local.py
from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Base de datos local en PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'email_db_local'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# En Local imprimimos los correos en la consola en lugar de enviarlos por SMTP
#EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# Para que sea enviado el correo habilitamos la siguiente linea 
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# API Key predeterminada para el Dashboard en entorno local
DEFAULT_DASHBOARD_API_KEY = env('DEFAULT_DASHBOARD_API_KEY', default='247fcfb9985edd0629c3b36e2cf11bdd09095322248da2e047982cc6e9098824')