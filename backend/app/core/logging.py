import logging
import sys

_FORMAT = "[%(asctime)s] %(message)s"
_DATEFMT = "%H:%M:%S"


def setup_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATEFMT))

    root = logging.getLogger("friday")
    root.setLevel(logging.INFO)
    root.handlers = [handler]
    root.propagate = False


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"friday.{name}")
