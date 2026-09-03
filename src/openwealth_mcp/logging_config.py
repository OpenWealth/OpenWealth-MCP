"""Logging helpers — JSON on stderr + optional rotating file (stdout stays MCP-clean)."""

from __future__ import annotations

import json
import logging
import re
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

_SECRET_RE = re.compile(r"(?i)\b(authorization|bearer|token|password|secret)\b\s*[:=]\s*([^\s,;]+)")
_BEARER_RE = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._\-]+")


class RedactingFilter(logging.Filter):
    """Strip bearer tokens and obvious secret assignments from log messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = _redact(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: _redact_value(v) for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(_redact_value(a) for a in record.args)
        return True


class JsonFormatter(logging.Formatter):
    """Minimal JSON log lines suitable for SIEM shippers."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in (
            "correlation_id",
            "operation",
            "status_code",
            "duration_ms",
            "path",
        ):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def _redact(text: str) -> str:
    text = _BEARER_RE.sub("Bearer ***", text)
    return _SECRET_RE.sub(r"\1=***", text)


def _redact_value(value: object) -> object:
    if isinstance(value, str):
        return _redact(value)
    return value


def setup_logging(
    level: str = "INFO",
    *,
    log_file: str | None = None,
) -> logging.Logger:
    """Configure JSON logging to stderr and optionally to a rotating file."""
    numeric = getattr(logging, level.upper(), logging.INFO)
    root = logging.getLogger()
    root.setLevel(numeric)
    root.handlers.clear()

    formatter = JsonFormatter()
    redactor = RedactingFilter()

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(formatter)
    stderr_handler.addFilter(redactor)
    root.addHandler(stderr_handler)

    resolved_file: Path | None = None
    if log_file:
        resolved_file = Path(log_file).expanduser()
        resolved_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            resolved_file,
            maxBytes=5_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        file_handler.addFilter(redactor)
        root.addHandler(file_handler)

    if numeric > logging.DEBUG:
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("mcp").setLevel(logging.WARNING)

    log = logging.getLogger("openwealth_mcp")
    if resolved_file is not None:
        log.info("File logging enabled path=%s", str(resolved_file.resolve()))
    return log


def get_logger(name: str | None = None) -> logging.Logger:
    return logging.getLogger(name or "openwealth_mcp")
