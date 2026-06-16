from .base import *
import os

DEBUG = False

# 生产环境必须设置 SECRET_KEY 环境变量
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError('生产环境必须设置 SECRET_KEY 环境变量')

# 生产环境必须配置 ALLOWED_HOSTS
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# ManifestStaticFilesStorage for cache-busting
STORAGES["staticfiles"]["BACKEND"] = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

# 生产环境安全配置
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'False').lower() == 'true'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# 生产环境日志写文件
LOGGING['loggers']['django']['handlers'] = ['console', 'file']
LOGGING['loggers']['news']['handlers'] = ['console', 'file']
LOGGING['loggers']['internal_auth']['handlers'] = ['console', 'file']

try:
    from .local import *
except ImportError:
    pass
