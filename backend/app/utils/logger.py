"""Central logging setup for the API process."""

import logging

import structlog


def setup_logging(level: str = "INFO") -> None:
    """Configure readable structured logs without emitting configuration secrets."""
    resolved_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(level=resolved_level, format="%(message)s", force=True)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(resolved_level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
