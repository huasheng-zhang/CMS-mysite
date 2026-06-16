from .base import *
import os

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: 此密钥仅用于开发环境，生产环境必须通过环境变量设置强密钥
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-dev-only-do-not-use-in-production-6^0%e-s64$(i!x0h$+)32'
)

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ["*"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


try:
    from .local import *
except ImportError:
    pass
