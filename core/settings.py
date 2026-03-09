"""
FAESA Voting System — Django Settings
"""

import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

# ── Security ───
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "change-me-in-production-faesa-hack")
DEBUG      = os.environ.get("DEBUG", "true").lower() == "true"

# Allows access from any host (required for ngrok / LAN)
ALLOWED_HOSTS = ["*"]

# ── Apps ─
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "api",
]

# ── Middleware 
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "core.urls"

# ── Database ─
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "voting.db",
    }
}

# ── Django REST Framework 
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "api.authentication.UsernameJWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.AllowAny",
    ),
}

# ── JWT 
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME":  timedelta(hours=8),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "AUTH_HEADER_TYPES":      ("Bearer",),
    "USER_ID_FIELD":          "id",
    "USER_ID_CLAIM":          "user_id",
    # Use stateless token validation — do not look up Django's auth.User
    "TOKEN_USER_CLASS":       "rest_framework_simplejwt.models.TokenUser",
}

# ── CORS 
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_HEADERS     = ["*"]

# ── Static / Frontend ───────────────────────────────────────────────────────
STATIC_URL       = "/frontend/"
STATICFILES_DIRS = [BASE_DIR / "frontend"]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS":    [BASE_DIR / "frontend"],
        "APP_DIRS": False,
        "OPTIONS": {"context_processors": []},
    },
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"