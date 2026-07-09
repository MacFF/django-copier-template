import os


# STORAGE CONFIG
AWS_S3_ACCESS_KEY_ID = os.getenv('S3_ACCESS_KEY_ID', '')
AWS_S3_SECRET_ACCESS_KEY = os.getenv('S3_SECRET_ACCESS_KEY', '')
AWS_S3_ENDPOINT_URL = os.getenv('S3_ENDPOINT_URL', '')
AWS_S3_CUSTOM_DOMAIN = os.getenv('S3_CUSTOM_DOMAIN', '')

S3_STATIC_BUCKET_NAME = os.getenv('S3_STATIC_BUCKET_NAME', '')
S3_STORAGE_BUCKET_NAME = os.getenv('S3_STORAGE_BUCKET_NAME', '')
S3_TEMP_BUCKET_NAME = os.getenv('S3_TEMP_BUCKET_NAME', '')

IS_DEVELOPMENT = os.getenv('DJANGO_ENVIRONMENT', 'development') == 'development'

STORAGES = {
    "default": {
        "BACKEND": "{{project_slug}}.base.storage.MediaStorage",
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage' if IS_DEVELOPMENT else '{{project_slug}}.base.storage.StaticStorage',
    },
    "tempfiles": {
        "BACKEND": "{{project_slug}}.base.storage.TemporaryStorage",
    },
}

ALLOWED_FILE_TYPES = [
    "image/jpeg",
    "image/png",
    "image/tif",
    "application/pdf",
    "application/msword",  # .doc
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
    "application/vnd.ms-excel",  # .xls
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
    "application/vnd.ms-powerpoint",  # .ppt
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # .pptx
]
