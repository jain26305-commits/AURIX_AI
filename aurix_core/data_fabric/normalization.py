"""
AURIX Enterprise Data Fabric — Data Normalization Engine
Phase 19 Core Implementation.
Preserves raw values while standardizing dates, currencies, units, and identifiers.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Optional, Tuple

from aurix_core.data_fabric.contracts import (
    CanonicalEntityType,
    NormalizedRecordEnvelope,
    SourceRecordEnvelope,
)


class DataNormalizer:
    """Enterprise normalizer for multi-system disparate data intake."""

    VERSION = "1.0.0"

    UNIT_CONVERSIONS = {
        "kg": {"kg": 1.0, "g": 1000.0, "lb": 2.20462, "oz": 35.274},
        "g": {"kg": 0.001, "g": 1.0, "lb": 0.00220462, "oz": 0.035274},
        "lb": {"kg": 0.453592, "g": 453.592, "lb": 1.0, "oz": 16.0},
        "pcs": {"pcs": 1.0, "units": 1.0, "ea": 1.0},
        "units": {"pcs": 1.0, "units": 1.0, "ea": 1.0},
        "ea": {"pcs": 1.0, "units": 1.0, "ea": 1.0},
    }

    CURRENCY_SYMBOLS = {
        "$": "USD",
        "€": "EUR",
        "£": "GBP",
        "₹": "INR",
        "¥": "JPY",
    }

    @classmethod
    def normalize_timestamp(cls, raw_val: Any) -> Optional[datetime]:
        """Convert arbitrary date/time representations to UTC datetime."""
        if raw_val is None:
            return None
        if isinstance(raw_val, datetime):
            return raw_val if raw_val.tzinfo else raw_val.replace(tzinfo=timezone.utc)
        if isinstance(raw_val, (int, float)):
            # Handle epoch timestamp (seconds vs milliseconds)
            if raw_val > 1e11:
                raw_val /= 1000.0
            return datetime.fromtimestamp(raw_val, tz=timezone.utc)

        str_val = str(raw_val).strip()
        if not str_val:
            return None

        # ISO format standard parsing
        try:
            cleaned = str_val.replace("Z", "+00:00")
            dt = datetime.fromisoformat(cleaned)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            pass

        # Fallback date formats
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d %H:%M:%S",
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%Y%m%d",
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(str_val, fmt)
                return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                continue

        return None

    @classmethod
    def normalize_currency_amount(cls, raw_val: Any, default_currency: str = "USD") -> Tuple[Decimal, str]:
        """Normalize currency string or number to clean Decimal and ISO currency code."""
        if raw_val is None:
            return Decimal("0.00"), default_currency

        if isinstance(raw_val, (int, float, Decimal)):
            return Decimal(str(raw_val)), default_currency

        str_val = str(raw_val).strip()
        detected_currency = default_currency

        for symbol, code in cls.CURRENCY_SYMBOLS.items():
            if symbol in str_val:
                detected_currency = code
                str_val = str_val.replace(symbol, "")
                break

        # Remove thousand commas and extraneous characters
        cleaned = re.sub(r"[^\d.-]", "", str_val)
        try:
            amount = Decimal(cleaned) if cleaned else Decimal("0.00")
        except InvalidOperation:
            amount = Decimal("0.00")

        return amount, detected_currency

    @classmethod
    def normalize_unit(cls, value: float, from_unit: str, to_unit: str) -> float:
        """Convert standard logistics and inventory units."""
        from_u = from_unit.lower().strip()
        to_u = to_unit.lower().strip()

        if from_u == to_u:
            return float(value)

        if from_u in cls.UNIT_CONVERSIONS and to_u in cls.UNIT_CONVERSIONS[from_u]:
            factor = cls.UNIT_CONVERSIONS[from_u][to_u]
            return float(value * factor)

        return float(value)

    @classmethod
    def normalize_identifier(cls, raw_id: Any) -> str:
        """Sanitize SKU, Customer, and Transaction identifiers."""
        if raw_id is None:
            return ""
        return str(raw_id).strip().upper()

    @classmethod
    def process_envelope(
        cls,
        envelope: SourceRecordEnvelope,
        canonical_type: CanonicalEntityType,
        canonical_id: str,
        mapping_rules: Optional[Dict[str, str]] = None,
    ) -> NormalizedRecordEnvelope:
        """Transform raw envelope into a standardized canonical envelope."""
        mapping = mapping_rules or {}
        raw = envelope.payload
        normalized: Dict[str, Any] = {}

        for k, v in raw.items():
            target_key = mapping.get(k, k)

            if "date" in target_key.lower() or "time" in target_key.lower() or "at" in target_key.lower():
                dt = cls.normalize_timestamp(v)
                normalized[target_key] = dt.isoformat() if dt else None
            elif "price" in target_key.lower() or "amount" in target_key.lower() or "cost" in target_key.lower() or "total" in target_key.lower():
                amt, curr = cls.normalize_currency_amount(v)
                normalized[target_key] = float(amt)
                if "currency" not in normalized:
                    normalized["currency"] = curr
            elif "id" in target_key.lower() or "sku" in target_key.lower() or "code" in target_key.lower():
                normalized[target_key] = cls.normalize_identifier(v)
            elif isinstance(v, str):
                normalized[target_key] = v.strip()
            else:
                normalized[target_key] = v

        return NormalizedRecordEnvelope(
            tenant_id=envelope.tenant_id,
            canonical_entity_type=canonical_type,
            canonical_id=canonical_id,
            source_system=envelope.source_system,
            source_record_id=envelope.source_record_id,
            transformation_version=cls.VERSION,
            normalized_data=normalized,
            source_data_snapshot=raw,
            lineage_metadata={
                "batch_id": envelope.ingestion_batch_id,
                "ingested_at": envelope.ingested_at.isoformat(),
                "transformer": "DataNormalizer_v1",
            },
        )
