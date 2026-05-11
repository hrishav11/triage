"""Structured logging configuration.

We use structlog so log records carry structured context (key=value pairs)
that we can grep, filter, and aggregate. This becomes critical when debugging
agent traces in later weeks.
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor

from triage.config import get_settings


def configure_logging() -> None:
    """Configure structlog with sensible defaults.

    In dev: human-readable colored output.
    In prod: JSON output (machine-parseable for log aggregation).
    """
    settings = get_settings()

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=settings.log_level,
    )

    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    processors: list[Processor]
    if settings.log_format == "json":
        processors = [*shared_processors, structlog.processors.JSONRenderer()]
    else:
        processors = [
            *shared_processors,
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, settings.log_level)),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> Any:
    """Get a configured logger instance.

    Returns Any because structlog's BoundLogger return type causes mypy
    conflicts with the actual runtime type. Safe to use — structlog is
    fully functional, this is a type-stub limitation.

    Usage:
        logger = get_logger(__name__)
        logger.info("processing case", case_id=123, phenotype_count=7)
    """
    return structlog.get_logger(name)
