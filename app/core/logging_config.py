"""
Logging configuration module
"""
import logging
import logging.config


def configure_logging():
    """Configure structured logging for the application"""

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": "logs/tagihan-wifi.log",
                "maxBytes": 10485760,  # 10 MB
                "backupCount": 5,
            },
        },
        "loggers": {
            "app": {
                "level": "DEBUG",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
        },
        "root": {
            "level": "INFO",
            "handlers": ["console", "file"],
        },
    }

    logging.config.dictConfig(logging_config)

    # Create logs directory if it doesn't exist
    import os
    os.makedirs("logs", exist_ok=True)
