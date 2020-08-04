"""
Django settings for cmdb project.

Generated by 'django-admin startproject' using Django 3.0.8.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

from corsheaders.defaults import default_headers
from .configs import cfg

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 配置目录和创建
LOG_DIR = os.path.join(BASE_DIR, 'logs/')
EXCEL_FILE_DIR = os.path.join(BASE_DIR, 'excel_files/')

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR, 0o755)


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = cfg.get('secret', 'secret_key')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'controller',
    'asset'
]

MIDDLEWARE = [
    'common.middleware.LoggingMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'cmdb.urls'

# WSGI 应用入口
WSGI_APPLICATION = 'cmdb.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases
DATABASES = {
     'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': cfg.get('mysql', 'db'),
        'HOST': cfg.get('mysql', 'host'),
        'PORT': cfg.get('mysql', 'port'),
        'USER': cfg.get('mysql', 'user'),
        'PASSWORD': cfg.get('mysql', 'password'),
        'ATOMIC_REQUESTS': True
    }
}
#

# 国际化配置
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

# 静态文件路由
STATIC_URL = '/static/'
# 静态文件收集的存放位置
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# 跨域配置，允许跨域的源
CORS_ORIGIN_WHITELIST = (
    'http://localhost:8080',
)

# 允许跨域的头部
CORS_ALLOW_HEADERS = default_headers + (
    'Access-Control-Allow-Origin',
)

# 允许跨域时访问 cookie
CORS_ALLOW_CREDENTIALS = True


# DRF 配置
REST_FRAMEWORK = {
    # 分页类
    'DEFAULT_PAGINATION_CLASS': 'common.paginations.PagePagesizePagination',
    # 异常处理
    'EXCEPTION_HANDLER': 'common.mixins.normalized_exception_handler',
    # 无验证时的用户
    'UNAUTHENTICATED_USER': 'common.auth.AnonymousUser',
    # 时间格式
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
    # 查询过滤器
    'DEFAULT_FILTER_BACKENDS': [
        'common.filters.QueryFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter'
    ]
}

# ASGI 应用入口
ASGI_APPLICATION = 'cmdb.routing.application'

# 日志配置
LOGGING = {
    'version': 1,
    # 禁用已经存在的日志器
    'disable_existing_loggers': False,
    # 日志格式器
    'formatters': {
        # 简单
        'simple': {
            'format': '[%(asctime)s][%(levelname)s][%(filename)s:%(lineno)d] -> %(message)s'
        },
        # 标准
        'standard': {
            'format': '[%(asctime)s][%(levelname)s][%(processName)s][%(threadName)s]'
                      '[%(filename)s:%(funcName)s:%(lineno)d] -> %(message)s'
        },
        # 详细的
        'verbose': {
            'format': '[%(asctime)s][%(levelname)s][%(processName)s:%(process)d][%(threadName)s:%(thread)d]'
                      '[%(pathname)s:%(funcName)s:%(lineno)d] -> %(message)s'
        }
    },
    # 过滤器
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    # 处理器
    'handlers': {
        # 输出 DEBUG 简单格式日志到终端
        'console': {
            'level': 'DEBUG',
            # 只有在 debug=True 时才生效
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        # 默认输出 DEBUG 标准格式日志到文件
        'default': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, "cmdb.log"),
            'maxBytes': 1024 * 1024 * 50,
            'backupCount': 3,
            'formatter': 'standard',
            'encoding': 'utf-8',
        },
        # 输出 DEBUG 详细格式日志到文件
        'error': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, "error.log"),
            'maxBytes': 1024 * 1024 * 50,
            'backupCount': 5,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
    },
    # 日志器
    'loggers': {
        # django 使用的日志器
        'django': {
            'handlers': ['console', 'default', 'error'],
            'level': 'INFO',
            # 是否向更高级别的日志器传递
            'propagate': True
        }
    }
}

LOGGER = 'django'