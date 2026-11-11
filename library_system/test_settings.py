"""Settings for isolated, disposable CI test databases."""

from . import settings

SECRET_KEY = settings.SECRET_KEY
INSTALLED_APPS = settings.INSTALLED_APPS
MIDDLEWARE = settings.MIDDLEWARE
ROOT_URLCONF = settings.ROOT_URLCONF
TEMPLATES = settings.TEMPLATES
STATIC_URL = settings.STATIC_URL
DEFAULT_AUTO_FIELD = settings.DEFAULT_AUTO_FIELD
LANGUAGE_CODE = settings.LANGUAGE_CODE
TIME_ZONE = settings.TIME_ZONE
USE_I18N = settings.USE_I18N
USE_TZ = settings.USE_TZ
LOGIN_REDIRECT_URL = settings.LOGIN_REDIRECT_URL
LOGOUT_REDIRECT_URL = settings.LOGOUT_REDIRECT_URL

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
MIGRATION_MODULES = {"library": None}
