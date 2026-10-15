"""Minimal settings for the django-naija example project (development only)."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "example-only-not-secret"  # noqa: S105 - example project, never deployed
DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rest_framework",
    "shop",
]

MIDDLEWARE = ["django.middleware.common.CommonMiddleware"]
ROOT_URLCONF = "example_site.urls"
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [], "APP_DIRS": True}]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
REST_FRAMEWORK = {"UNAUTHENTICATED_USER": None}
