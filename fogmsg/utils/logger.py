import logging

LOGLEVEL = "debug"
LOGFILE = ""


def configure_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.hasHandlers():
        # already configured
        return logger

    levels = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warn": logging.WARN,
        "critical": logging.CRITICAL,
    }
    logger.setLevel(levels[LOGLEVEL])

    if LOGFILE:
        handler = logging.FileHandler(LOGFILE)
    else:
        handler = logging.StreamHandler()

    handler.setLevel(levels[LOGLEVEL])

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s (%(threadName)-9s) - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger
