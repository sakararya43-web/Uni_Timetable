import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

request_id_ctx_var: ContextVar[str] = ContextVar("request_id", default="system")


class JSONLogFormatter(logging.Formatter):
    """Formats log records as clean single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "requestId": request_id_ctx_var.get(),
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logging(debug: bool = False) -> logging.Logger:
    level = logging.DEBUG if debug else logging.INFO
    logger = logging.getLogger("exam_scheduler")
    logger.setLevel(level)

    # Avoid duplicate handlers on reload
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONLogFormatter())
        logger.addHandler(handler)

    return logger
