from __future__ import annotations

import logging
import re

import structlog

from app.config import settings

_TOKEN_RE = re.compile(re.escape(settings.BOT_TOKEN)) if settings.BOT_TOKEN else None


def _redact_token(_logger: object, _method_name: str, event_dict: dict) -> dict:
    if _TOKEN_RE is None:
        return event_dict
    for key, value in list(event_dict.items()):
        if isinstance(value, str) and _TOKEN_RE.search(value):
            event_dict[key] = _TOKEN_RE.sub("***REDACTED***", value)
    return event_dict


def configure_logging() -> None:
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format="%(message)s",
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            _redact_token,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(settings.LOG_LEVEL)),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
