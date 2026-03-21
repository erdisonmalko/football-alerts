import logging
import logging.config

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
    },
    "root": {
        "level": "DEBUG",  # App logs default level
        "handlers": ["console"],
    },
    "loggers": {
        "app": {
            "level": "DEBUG",
            "handlers": ["console"],
            "propagate": False,
        },
        "sqlalchemy.engine": {"level": "WARNING", "propagate": False},
        "httpx": {"level": "WARNING"},
        "httpcore": {"level": "WARNING"},
        "uvicorn.access": {"level": "WARNING"},
    },
}


def setup_logging():
    logging.config.dictConfig(LOGGING_CONFIG)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
