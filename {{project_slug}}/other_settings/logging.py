LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,  # สำคัญมาก
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
