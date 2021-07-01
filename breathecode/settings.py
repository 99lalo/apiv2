"""
Django settings for breathecode project.
Generated by 'django-admin startproject' using Django 3.0.7.
For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/
For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os
import django_heroku
import dj_database_url
import sys
import logging
from django.contrib.messages import constants as messages
from django.utils.log import DEFAULT_LOGGING
# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

DATABASE_URL = os.environ.get('DATABASE_URL')
ENVIRONMENT = os.environ.get('ENV')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '5ar3h@ha%y*dc72z=8-ju7@4xqm0o59*@k*c2i=xacmy2r=%4a'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = (ENVIRONMENT == 'development')

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    'breathecode.admin_styles',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.postgres',
    'rest_framework',
    'phonenumber_field',
    'drf_yasg',
    'corsheaders',
    'breathecode.authenticate',
    'breathecode.admissions',
    'breathecode.events',
    'breathecode.feedback',
    'breathecode.notify',
    'breathecode.assignments',
    'breathecode.marketing',
    'breathecode.freelance',
    'breathecode.certificate',
    'breathecode.monitoring',
    'breathecode.media',
    'breathecode.assessment',
    'breathecode.registry',
]

REST_FRAMEWORK = {
    'DEFAULT_VERSIONING_CLASS':
    'rest_framework.versioning.NamespaceVersioning',
    'DEFAULT_PAGINATION_CLASS':
    'breathecode.utils.HeaderLimitOffsetPagination',
    'EXCEPTION_HANDLER':
    'breathecode.utils.breathecode_exception_handler',
    'PAGE_SIZE':
    100,
    'DEFAULT_VERSION':
    'v1',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'breathecode.authenticate.authentication.ExpiringTokenAuthentication',
        # 'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        # 'rest_framework.permissions.AllowAny',
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework_csv.renderers.CSVRenderer',
    ),
}

MIDDLEWARE = [
    # 'rollbar.contrib.django.middleware.RollbarNotifierMiddlewareOnly404',
    # ⬆ This Rollbar should always be first please!
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',

    # Cache
    # 'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.cache.FetchFromCacheMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'breathecode.utils.admin_timezone.TimezoneMiddleware',

    # ⬇ Rollbar is always last please!
    # 'rollbar.contrib.django.middleware.RollbarNotifierMiddlewareExcluding404',
]

AUTHENTICATION_BACKENDS = ('django.contrib.auth.backends.ModelBackend', )

ROOT_URLCONF = 'breathecode.urls'

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
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'breathecode.wsgi.application'

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME':
        'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Disable Django's logging setup
LOGGING_CONFIG = None

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            # exact format is not important, this is the minimum information
            'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        },
        'django.server': DEFAULT_LOGGING['formatters']['django.server'],
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        # console logs to stderr
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        },
        # Add Handler for Rollbar
        # 'rollbar': {
        #     'filters': ['require_debug_false'],
        #     'access_token': os.getenv('ROLLBAR_ACCESS_TOKEN', ""),
        #     'environment': ENVIRONMENT,
        #     'class': 'rollbar.logger.RollbarHandler',
        # },
        'django.server': DEFAULT_LOGGING['handlers']['django.server'],
    },
    'loggers': {
        # default for all undefined Python modules
        '': {
            'level': 'WARNING',
            # 'handlers': ['console', 'rollbar'],
            'handlers': ['console'],
        },
        # Our application code
        'breathecode': {
            'level': LOG_LEVEL,
            # 'handlers': ['console', 'rollbar'],
            'handlers': ['console'],
            # Avoid double logging because of root logger
            'propagate': False,
        },
        # Prevent noisy modules from logging to Sentry
        'noisy_module': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': False,
        },
        # Default runserver request logging
        'django.server': DEFAULT_LOGGING['loggers']['django.server'],
    },
})

ROLLBAR = {
    'access_token':
    os.getenv('ROLLBAR_ACCESS_TOKEN', ''),
    'environment':
    'development' if DEBUG else 'production',
    'branch':
    'master',
    'root':
    BASE_DIR,
    # parsed POST variables placed in your output for exception handling
    'EXCEPTION_HANDLER':
    'rollbar.contrib.django_rest_framework.post_exception_handler',
}

MESSAGE_TAGS = {
    messages.DEBUG: 'alert-info',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR: 'alert-danger',
}

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Allow all host headers
ALLOWED_HOSTS = ['*']

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_ROOT = os.path.join(PROJECT_ROOT, 'staticfiles')
STATIC_URL = '/static/'

# Extra places for collectstatic to find static files.
STATICFILES_DIRS = [
    os.path.join(PROJECT_ROOT, 'static'),
]

CORS_ORIGIN_ALLOW_ALL = True

CORS_ALLOW_HEADERS = [
    'accept',
    'academy',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'cache-control',
    'credentials',
    'http-access-control-request-method',
]

REDIS_URL = os.getenv('REDIS_URL', '')


def cache_opts(is_test_env):
    if is_test_env:
        return {'OPTIONS': {}}
    else:
        return {
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'PARSER_CLASS': 'redis.connection.HiredisParser',
            }
        }


is_test_env = os.getenv('ENV') == 'test'
CACHES = {
    'default': {
        'BACKEND':
        'django.core.cache.backends.locmem.LocMemCache'
        if is_test_env else 'django_redis.cache.RedisCache',
        'LOCATION':
        'breathecode' if is_test_env else [REDIS_URL],
        # **cache_opts(is_test_env),
    },
}

CACHE_MIDDLEWARE_SECONDS = 60 * int(os.getenv('CACHE_MIDDLEWARE_MINUTES', 120))

# Simplified static file serving.
# https://warehouse.python.org/project/whitenoise/
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

SITE_ID = 1

_locals = locals()
django_heroku.settings(_locals)

# Change 'default' database configuration with $DATABASE_URL.
# https://github.com/jacobian/dj-database-url#url-schema
DATABASES = {
    'default': dj_database_url.config(default=DATABASE_URL),
}
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'
