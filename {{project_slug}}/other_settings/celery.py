import os

REDIS_BROKER_URL = os.getenv('REDIS_BROKER_URL', 'redis://localhost:6379/1')
RABBIT_BROKER_URL = os.getenv('RABBIT_BROKER_URL', 'amqp://guest:guest@localhost:5672//')

# CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/3")

CELERY_TIMEZONE = "Asia/Bangkok"
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_RESULT_SERIALIZER = 'json'
