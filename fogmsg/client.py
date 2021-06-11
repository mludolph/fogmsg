import logging
from os import path
import sys

sys.path.append(path.join(path.dirname(__file__), ".."))

from fogmsg.utils.logger import configure_logger  # noqa

logger = logging.getLogger(path.basename(__file__))
logger = configure_logger(logger)

if __name__ == "__main__":

    logger.info("STARTING FOGMSG")
