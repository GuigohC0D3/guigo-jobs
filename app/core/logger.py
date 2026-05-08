import logging
import sys
from pathlib import Path

from rich.logging import RichHandler

from app.core.config import settings


def setup_logger(name: str = "guigo") -> logging.Logger:
    log_path = settings.logs_dir / "guigo.log"

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    if logger.handlers:
        return logger

    rich_handler = RichHandler(
        rich_tracebacks=True,
        show_path=False,
        markup=True,
    )
    rich_handler.setLevel(logging.WARNING)

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    )
    file_handler.setLevel(logging.DEBUG)

    logger.addHandler(rich_handler)
    logger.addHandler(file_handler)

    return logger


logger = setup_logger()
