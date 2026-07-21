import json
import logging
from contextvars import ContextVar
from datetime import datetime, timezone


request_id_context = ContextVar("request_id", default="-")


class JsonFormatter(logging.Formatter):
    """Format logs as one JSON object per line for local and hosted collectors."""

    reserved = {
        "args", "asctime", "created", "exc_info", "exc_text", "filename",
        "funcName", "levelname", "levelno", "lineno", "module", "msecs",
        "message", "msg", "name", "pathname", "process", "processName",
        "relativeCreated", "stack_info", "thread", "threadName", "taskName",
    }

    def format(self, record):
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(
                record,
                "request_id",
                request_id_context.get(),
            ),
        }
        payload.update(
            {
                key: value
                for key, value in record.__dict__.items()
                if key not in self.reserved
                and not key.startswith("_")
                and key not in payload
                and isinstance(value, (str, int, float, bool, type(None)))
            }
        )
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str, ensure_ascii=False)
