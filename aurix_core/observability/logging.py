"""Structured JSON Logging Formatter and Telemetry Integration for AURIX Enterprise Platform."""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict


class StructuredJsonFormatter(logging.Formatter):
    """Custom logging formatter that outputs logs in structured JSON format with secret scrubbing."""

    SENSITIVE_KEYS = {"password", "secret", "token", "api_key", "authorization", "key", "credential"}

    def format(self, record: logging.LogRecord) -> str:
        """Formats log records into a JSON string containing context metadata and scrubbed payloads."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "environment": os.getenv("ENVIRONMENT", "development"),
        }

        # Extract contextual attributes if present in log record or extras
        for attr in [
            "request_id",
            "correlation_id",
            "tenant_id",
            "user_id",
            "run_id",
            "action_id",
            "event_id",
            "connector_id",
            "capability",
            "duration",
            "outcome",
        ]:
            if hasattr(record, attr):
                log_data[attr] = getattr(record, attr)

        # Scrub sensitive keys if extra payload or args are provided
        if record.args and isinstance(record.args, dict):
            log_data["args"] = self._scrub_sensitive_data(record.args)

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)

    def _scrub_sensitive_data(self, data: Any) -> Any:
        """Recursively scrubs sensitive keys from dictionaries or lists."""
        if isinstance(data, dict):
            scrubbed = {}
            for k, v in data.items():
                if any(s in k.lower() for s in self.SENSITIVE_KEYS):
                    scrubbed[k] = "[REDACTED]"
                else:
                    scrubbed[k] = self._scrub_sensitive_data(v)
            return scrubbed
        elif isinstance(data, list):
            return [self._scrub_sensitive_data(item) for item in data]
        return data


def setup_structured_logging(level: int = logging.INFO) -> None:
    """Configures root logger with structured JSON formatter."""
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredJsonFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)
    root_logger.addHandler(handler)
