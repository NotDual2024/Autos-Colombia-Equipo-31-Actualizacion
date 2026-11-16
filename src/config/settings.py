"""Configuración del proyecto Django - Parqueadero "Autos Colombia".

Ejecución local (P-09). Los valores sensibles se pueden sobrescribir con
variables de entorno; los valores por defecto solo sirven para desarrollo local.
"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "solo-desarrollo-local-no-usar-en-produccion")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Módulos del sistema (Arquitectura v1, sección 4). No se habilita django.contrib.admin (DEC-011).
    "apps.core.apps.CoreConfig",
    "apps.cuentas.apps.CuentasConfig",
    "apps.usuarios_celdas.apps.UsuariosCeldasConfig",
    "apps.pagos.apps.PagosConfig",
    "apps.entradas_salidas.apps.EntradasSalidasConfig",
    "apps.novedades.apps.NovedadesConfig",
    "apps.notificaciones.apps.NotificacionesConfig",
    "apps.demo.apps.DemoConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.contexto_general",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ.get("DJANGO_DB_PATH", str(BASE_DIR / "db.sqlite3")),
    }
}

# --- Autenticación (RNF-001, RNF-002, DEC-012) ---
AUTH_USER_MODEL = "cuentas.Usuario"
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.ScryptPasswordHasher",
]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LOGIN_URL = "cuentas:login"
LOGIN_REDIRECT_URL = "entradas_salidas:entrada"
LOGOUT_REDIRECT_URL = "cuentas:login"

# --- Idioma y zona horaria (Arquitectura 7.3, DM-07) ---
LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Planificador de avisos (DEC-008) ---
# Se puede desactivar con AVISOS_PLANIFICADOR=0 (por ejemplo, para depurar).
AVISOS_PLANIFICADOR_ACTIVO = os.environ.get("AVISOS_PLANIFICADOR", "1") == "1"
AVISOS_INTERVALO_MINUTOS = 60

# --- Nombre visible del sistema ---
NOMBRE_SISTEMA = "Autos Colombia"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"simple": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"}},
    "handlers": {"consola": {"class": "logging.StreamHandler", "formatter": "simple"}},
    "loggers": {
        # Durante las pruebas solo se muestran advertencias (los correos simulados no ensucian la salida).
        "apps": {"handlers": ["consola"], "level": "WARNING" if "test" in sys.argv else "INFO"},
        "apscheduler": {"handlers": ["consola"], "level": "WARNING"},
    },
}
