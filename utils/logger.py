import logging
import sys
from config import settings


def setup_logger() -> logging.Logger:
    """Configures structured application logging."""
    logger = logging.getLogger("StickerManagerBot")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    log_file = settings.LOGS_DIRECTORY / "bot.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


logger = setup_logger()
