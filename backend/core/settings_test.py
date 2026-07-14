from .settings import *  # noqa: F403, F401

DEBUG = False

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
DEFAULT_FILE_STORAGE = "django.core.files.storage.InMemoryStorage"

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.spatialite",
        "NAME": ":memory:",
    }
}

SPATIALITE_LIBRARY_PATH = "/usr/lib/x86_64-linux-gnu/mod_spatialite.so"
