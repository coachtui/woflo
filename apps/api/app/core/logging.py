import logging
import sys

from pythonjsonlogger import jsonlogger


def configure_logging() -> None:
    """Configure structured JSON logging."""

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    handler.setFormatter(formatter)

    # Replace any default handlers
    root.handlers = [handler]
