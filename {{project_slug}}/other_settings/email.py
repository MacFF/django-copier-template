import os

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'localhost')
EMAIL_PORT = os.getenv('EMAIL_PORT', 587)
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "temp.ricecert@gmail.com")
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() == "true"
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "False").lower() == "true"

DEFAULT_FROM_EMAIL = f"No-Reply DRR System <{EMAIL_HOST_USER}>"

FRONTEND_URL_SET_PASSWORD = os.getenv("FRONTEND_URL_SET_PASSWORD", "http://localhost:5173")
