"""
AURIX Enterprise Agent Studio — Safe Secret Reference Manager
Phase 30 Core Implementation.
Enforces credential redaction and ensures workflows reference SECRET_REF_ID without storing raw credentials.
"""

from __future__ import annotations

import re
from typing import Any, Dict


class StudioSecretManager:
    """Validates and sanitizes workflow payloads to prevent credential leakage."""

    SECRET_PATTERN = re.compile(r"^SECRET_REF_[A-Z0-9_]+$")

    @classmethod
    def sanitize_config_for_export(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        """Redact sensitive fields and ensure secrets are stored only as references."""
        sanitized = config.copy()
        for k, v in sanitized.items():
            if any(term in k.lower() for term in ["password", "token", "secret", "api_key", "key"]):
                if isinstance(v, str) and not cls.SECRET_PATTERN.match(v):
                    sanitized[k] = f"SECRET_REF_{k.upper()}"
        return sanitized
