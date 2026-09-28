"""
Django settings ba projetu SMKRE
Sistema Monitorizasaun Konflitu Rai no Eviksaun - Rede ba Rai

Konfigurasaun hotu lee husi file .env (haree .env.example).
Seksaun sira iha numeru, atu fasil buka bainhira iha erru:
	1. Seguransa            7. Session & Login
	2. Aplikasaun           8. REST Framework & JWT (sinkron offline)
	3. Template             9. Email
	4. Database            10. Redis & Celery
	5. Password (Argon2)   11. Logging
	6. Lian & Static       12. Seguransa production (HTTPS, CSP)
"""

from pathlib import Path
from datetime import timedelta
from decouple import config as env, Csv
from django.conf.locale import LANG_INFO
from django.contrib.messages import constants as message_constants
from csp.constants import NONCE, NONE, SELF

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# ══════════════════════════════════════════════
# 1. SEGURANSA
# ══════════════════════════════════════════════
SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = env('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())
CSRF_TRUSTED_ORIGINS = env('CSRF_TRUSTED_ORIGINS', default='', cast=Csv())

# Password default ba utilizador foun / reset (tenke troka iha login dahuluk)
DEFAULT_PASSWORD = env('DEFAULT_PASSWORD')

# URL admin Django la uza "/admin/" (atu la fasil buka)
ADMIN_URL = env('ADMIN_URL', default='jestaun-smkre/')


# ══════════════════════════════════════════════
# 2. APLIKASAUN
# ══════════════════════════════════════════════
INSTALLED_APPS = [
	# Django
	'django.contrib.admin',
	'django.contrib.auth',
	'django.contrib.contenttypes',
	'django.contrib.sessions',
	'django.contrib.messages',
	'whitenoise.runserver_nostatic',
	'django.contrib.staticfiles',
	'django.contrib.humanize',

	# Third-party
	'rest_framework',
	'rest_framework_simplejwt',
	'rest_framework_simplejwt.token_blacklist',
	'crispy_forms',
	'crispy_bootstrap4',
	'axes',                                   # limite login sala
	'csp',                                    # Content-Security-Policy
	'django_celery_beat',                     # knaar automátiku (horáriu)

	# SMKRE
	'main.apps.MainConfig',
	'config.apps.ConfigConfig',
	'custom.apps.CustomConfig',
	'users.apps.UsersConfig',
	'notification.apps.NotificationConfig',
	'kazu.apps.KazuConfig',
	'report.apps.ReportConfig',
	'sinkron.apps.SinkronConfig',
	'legal.apps.LegalConfig',
	'publiku.apps.PublikuConfig',

	'django_cleanup.apps.CleanupConfig',      # hamoos file tuan automátiku (tenke ikus)
]

MIDDLEWARE = [
	'django.middleware.security.SecurityMiddleware',
	'whitenoise.middleware.WhiteNoiseMiddleware',            # static file iha production
	'django.contrib.sessions.middleware.SessionMiddleware',
	'django.middleware.locale.LocaleMiddleware',             # 4 lian
	'django.middleware.common.CommonMiddleware',
	'django.middleware.csrf.CsrfViewMiddleware',
	'django.contrib.auth.middleware.AuthenticationMiddleware',
	'django.contrib.messages.middleware.MessageMiddleware',
	'django.middleware.clickjacking.XFrameOptionsMiddleware',
	'csp.middleware.CSPMiddleware',
	'axes.middleware.AxesMiddleware',
	'smkre.middleware.SecurityHeadersMiddleware',
	'smkre.middleware.PreviousURLMiddleware',
	'smkre.middleware.NoBackAfterLogout',
	'smkre.middleware.ForceChangePasswordMiddleware',
]

ROOT_URLCONF = 'smkre.urls'
WSGI_APPLICATION = 'smkre.wsgi.application'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ══════════════════════════════════════════════
# 3. TEMPLATE
# ══════════════════════════════════════════════
TEMPLATES = [
	{
		'BACKEND': 'django.template.backends.django.DjangoTemplates',
		'DIRS': [BASE_DIR / 'templates'],     # override template third-party (ezemplu crispy)
		'APP_DIRS': True,
		'OPTIONS': {
			'context_processors': [
				'django.template.context_processors.debug',
				'django.template.context_processors.request',
				'django.template.context_processors.i18n',
				'django.contrib.auth.context_processors.auth',
				'django.contrib.messages.context_processors.messages',
				'csp.context_processors.nonce',
				'config.context_processors.smkre',
			],
		},
	},
]

CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap4'
CRISPY_TEMPLATE_PACK = 'bootstrap4'

MESSAGE_TAGS = {
	message_constants.DEBUG: 'debug',
	message_constants.INFO: 'info',
	message_constants.SUCCESS: 'success',
	message_constants.WARNING: 'warning',
	message_constants.ERROR: 'danger',
}


# ══════════════════════════════════════════════
# 4. DATABASE  (DEV: SQLite  |  PROD: PostgreSQL)
# ══════════════════════════════════════════════
if env('DB_ENGINE', default='sqlite') == 'postgresql':
	DATABASES = {
		'default': {
			'ENGINE': 'django.db.backends.postgresql',
			'NAME': env('DB_NAME'),
			'USER': env('DB_USER'),
			'PASSWORD': env('DB_PASSWORD'),
			'HOST': env('DB_HOST', default='localhost'),
			'PORT': env('DB_PORT', default='5432'),
			'CONN_MAX_AGE': 60,
		}
	}
else:
	DATABASES = {
		'default': {
			'ENGINE': 'django.db.backends.sqlite3',
			'NAME': BASE_DIR / 'db.sqlite3',
		}
	}


# ══════════════════════════════════════════════
# 5. PASSWORD (Argon2)
# ══════════════════════════════════════════════
PASSWORD_HASHERS = [
	'django.contrib.auth.hashers.Argon2PasswordHasher',     # prinsipál
	'django.contrib.auth.hashers.PBKDF2PasswordHasher',     # rezerva
]

AUTH_PASSWORD_VALIDATORS = [
	{'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
	{'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
	{'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
	{'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
	{'NAME': 'users.validators.NotDefaultPasswordValidator'},
]

AUTHENTICATION_BACKENDS = [
	'axes.backends.AxesStandaloneBackend',   # xave konta hafoin sala dala 5
	'django.contrib.auth.backends.ModelBackend',
]


# ══════════════════════════════════════════════
# 6. LIAN (Tetun default + PT, EN, ID) & STATIC / MEDIA
# ══════════════════════════════════════════════
# Django la iha Tetun, entaun ita aumenta rasik
LANG_INFO['tet'] = {'bidi': False, 'code': 'tet', 'name': 'Tetum', 'name_local': 'Tetun'}

LANGUAGE_CODE = 'tet'
LANGUAGES = [
	('tet', 'Tetun'),
	('pt', 'Português'),
	('en', 'English'),
	('id', 'Bahasa Indonesia'),
]
LOCALE_PATHS = [BASE_DIR / 'locale']
LANGUAGE_COOKIE_NAME = 'smkre_lian'
LANGUAGE_COOKIE_AGE = 60 * 60 * 24 * 365
TIME_ZONE = 'Asia/Dili'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
	'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
	'staticfiles': {
		'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage' if DEBUG
		else 'whitenoise.storage.CompressedManifestStaticFilesStorage',
	},
}

# Media (foto, vídeo, dokumentu) — LA serve direta; asesu liuhusi login deit
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 60 * 1024 * 1024


# ══════════════════════════════════════════════
# 7. SESSION & LOGIN
# ══════════════════════════════════════════════
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'login'

SESSION_COOKIE_AGE = 60 * 60 * 8                 # oras 8 (loron servisu ida)
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
PASSWORD_RESET_TIMEOUT = 60 * 60                 # link reset validu oras 1

# Limite login sala (django-axes)
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(minutes=30)
AXES_LOCKOUT_PARAMETERS = [['username', 'ip_address']]
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_TEMPLATE = 'home/lockout.html'
AXES_CLIENT_IP_CALLABLE = 'config.utils.get_client_ip'   # IP loos iha kotuk Nginx

# Server iha kotuk Nginx (production): IP kliente husi X-Forwarded-For ne'ebé Nginx hatama
BEHIND_PROXY = env('BEHIND_PROXY', default=not DEBUG, cast=bool)

# Autorizasaun offline (loron)
OFFLINE_PERMISSION_DAYS = env('OFFLINE_PERMISSION_DAYS', default=7, cast=int)

# Portal públiku: kontaktu iha topbar (ezemplu; troka iha .env ho kontaktu loloos; mamuk = la hatudu)
PORTAL_TELEFONE = env('PORTAL_TELEFONE', default='+670 0000 0000')
PORTAL_EMAIL = env('PORTAL_EMAIL', default='email@exemplu.tl')
PORTAL_ENDERESU = env('PORTAL_ENDERESU', default='Dili, Timor-Leste')
PORTAL_LIMITE_SUBAR = 3              # númeru 1–2 hatudu "< 3" (privasidade)


# ══════════════════════════════════════════════
# 8. REST FRAMEWORK & JWT (sinkron offline)
# ══════════════════════════════════════════════
REST_FRAMEWORK = {
	'DEFAULT_AUTHENTICATION_CLASSES': [
		'rest_framework.authentication.SessionAuthentication',
		'rest_framework_simplejwt.authentication.JWTAuthentication',
	],
	'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
	'DEFAULT_THROTTLE_CLASSES': ['rest_framework.throttling.UserRateThrottle'],
	'DEFAULT_THROTTLE_RATES': {'user': '300/minute', 'anon': '120/minute'},
}

SIMPLE_JWT = {
	'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
	'REFRESH_TOKEN_LIFETIME': timedelta(days=OFFLINE_PERMISSION_DAYS),
	'ROTATE_REFRESH_TOKENS': True,
	'BLACKLIST_AFTER_ROTATION': True,
	'UPDATE_LAST_LOGIN': True,
}


# ══════════════════════════════════════════════
# 9. EMAIL
# ══════════════════════════════════════════════
# DEV: email hatudu iha console. PROD: SMTP (Gmail ho App Password ka email organizasaun)
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = env('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='SMKRE Rede ba Rai <noreply@localhost>')
SERVER_EMAIL = DEFAULT_FROM_EMAIL
EMAIL_TIMEOUT = 20
SITE_URL = env('SITE_URL', default='http://127.0.0.1:8000')


# ══════════════════════════════════════════════
# 10. REDIS & CELERY
# ══════════════════════════════════════════════
REDIS_URL = env('REDIS_URL', default='redis://127.0.0.1:6379/0')
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TIME_LIMIT = 60 * 10
# DEV: la presiza Redis — knaar la'o kedas (la iha kotuk)
CELERY_TASK_ALWAYS_EAGER = env('CELERY_ALWAYS_EAGER', default=True, cast=bool)
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

if env('USE_REDIS_CACHE', default=False, cast=bool):
	CACHES = {'default': {'BACKEND': 'django.core.cache.backends.redis.RedisCache', 'LOCATION': REDIS_URL}}
else:
	CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}


# ══════════════════════════════════════════════
# 11. LOGGING  (logs/error.log, logs/sinkron.log, logs/seguransa.log)
# ══════════════════════════════════════════════
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
	'version': 1,
	'disable_existing_loggers': False,
	'formatters': {
		'detail': {'format': '[{asctime}] {levelname} {name} {module}:{lineno} — {message}', 'style': '{'},
		'simple': {'format': '[{asctime}] {levelname} {message}', 'style': '{'},
	},
	'handlers': {
		'console': {'class': 'logging.StreamHandler', 'formatter': 'simple'},
		'error_file': {
			'class': 'logging.handlers.RotatingFileHandler', 'filename': LOG_DIR / 'error.log',
			'maxBytes': 5 * 1024 * 1024, 'backupCount': 10, 'formatter': 'detail', 'level': 'ERROR',
		},
		'sinkron_file': {
			'class': 'logging.handlers.RotatingFileHandler', 'filename': LOG_DIR / 'sinkron.log',
			'maxBytes': 5 * 1024 * 1024, 'backupCount': 10, 'formatter': 'detail',
		},
		'seguransa_file': {
			'class': 'logging.handlers.RotatingFileHandler', 'filename': LOG_DIR / 'seguransa.log',
			'maxBytes': 5 * 1024 * 1024, 'backupCount': 10, 'formatter': 'detail',
		},
	},
	'loggers': {
		'django': {'handlers': ['console', 'error_file'], 'level': 'INFO'},
		'smkre.sinkron': {'handlers': ['console', 'sinkron_file'], 'level': 'INFO', 'propagate': False},
		'smkre.seguransa': {'handlers': ['console', 'seguransa_file'], 'level': 'INFO', 'propagate': False},
		'axes': {'handlers': ['console', 'seguransa_file'], 'level': 'WARNING', 'propagate': False},
		'smkre': {'handlers': ['console', 'error_file'], 'level': 'INFO'},
	},
}


# ══════════════════════════════════════════════
# 12. SEGURANSA PRODUCTION (HTTPS, cookie, CSP)
# ══════════════════════════════════════════════
X_FRAME_OPTIONS = 'SAMEORIGIN'   # SAMEORIGIN (la'ós DENY): Document Vault sei hatudu PDF iha iframe husi SMKRE rasik
SILENCED_SYSTEM_CHECKS = ['security.W019']
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# Kamera no GPS deit permite husi SMKRE rasik (haree smkre/middleware.py)
PERMISSIONS_POLICY = 'camera=(self), geolocation=(self), microphone=(self), payment=(), usb=()'

# Content-Security-Policy: JS/CSS husi server SMKRE deit (aset lokál hotu)
CONTENT_SECURITY_POLICY = {
	'DIRECTIVES': {
		'default-src': [SELF],
		'script-src': [SELF, NONCE],
		'style-src': [SELF, "'unsafe-inline'"],
		'img-src': [SELF, 'data:', 'blob:', 'https://*.tile.openstreetmap.org', 'https://server.arcgisonline.com'],
		'font-src': [SELF],
		'connect-src': [SELF],
		'media-src': [SELF, 'blob:'],
		'worker-src': [SELF],
		'manifest-src': [SELF],
		'frame-ancestors': [SELF],
		'form-action': [SELF],
		'base-uri': [SELF],
		'object-src': [NONE],
	},
}

if not DEBUG:
	SECURE_SSL_REDIRECT = env('SECURE_SSL_REDIRECT', default=True, cast=bool)
	SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
	SESSION_COOKIE_SECURE = True
	CSRF_COOKIE_SECURE = True
	SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365
	SECURE_HSTS_INCLUDE_SUBDOMAINS = True
	SECURE_HSTS_PRELOAD = True
