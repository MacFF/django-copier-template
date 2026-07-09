import os
from {{project_slug}}.base.functions import strtobool
from corsheaders.defaults import default_headers


# CORE CONFIG
CORS_ALLOW_CREDENTIALS = os.getenv('DJANGO_ENVIRONMENT', 'development') == 'development'
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:3000').split(",")
CORS_ALLOWED_ORIGIN_REGEXES = os.getenv('CORS_ALLOWED_ORIGIN_REGEXES', r'^http://localhost:\d+$').split(",")
CORS_ALLOW_ALL_ORIGINS = strtobool(os.getenv('CORS_ALLOW_ALL_ORIGINS', 'True'))
CUSTOM_HEADERS = os.getenv('CORS_CUSTOM_HEADERS', 'X-Latitude,X-Longitude,X-Language').split(",")

CORS_ALLOW_HEADERS = (
    *default_headers,
    *CUSTOM_HEADERS,
)
