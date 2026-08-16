"""Conservative locale-aware normalization for messy enterprise onboarding data."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Tuple, cast

import pandas as pd


DATE_COLUMN_HINTS = (
    "date",
    "time",
    "timestamp",
    "eta",
    "delivery",
    "ship",
    "order_date",
    "req_date",
)

NUMERIC_COLUMN_HINTS = (
    "qty",
    "quantity",
    "amount",
    "cost",
    "price",
    "value",
    "inventory",
    "stock",
    "demand",
    "sales",
    "units",
    "lead_time",
    "capacity",
    "weight",
    "volume",
    "rate",
    "percent",
    "pct",
)

CURRENCY_SYMBOLS = {
    "$": "USD",
    "€": "EUR",
    "£": "GBP",
    "¥": "JPY",
    "₹": "INR",
}

_DATE_LIKE_RE = re.compile(
    r"^\s*(?:\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}|\d{4}[-/.]\d{1,2}[-/.]\d{1,2}"
    r"(?:[ T]\d{1,2}:\d{2}(?::\d{2})?)?)\s*$"
)

_CURRENCY_RE = re.compile(r"[^0-9,.-]+")


class EnterpriseNormalizationEngine:
    """Normalizes only values that can be transformed without fabricating meaning."""

    @staticmethod
    def _is_date_column(column: str) -> bool:
        cleaned = column.strip().lower().replace(" ", "_")
        return any(hint in cleaned for hint in DATE_COLUMN_HINTS)

    @staticmethod
    def _is_numeric_column(column: str) -> bool:
        cleaned = column.strip().lower().replace(" ", "_")
        return any(hint in cleaned for hint in NUMERIC_COLUMN_HINTS)

    @staticmethod
    def _normalize_numeric(value: Any) -> Any:
        if isinstance(value, bool) or value is None:
            return value

        if isinstance(value, (int, float)):
            return value

        raw = str(value).strip()
        if not raw:
            return value

        cleaned = _CURRENCY_RE.sub("", raw)
        if not re.search(r"\d", cleaned):
            return value

        # European style: 1.234,50 -> 1234.50
        if (
            "," in cleaned
            and "." in cleaned
            and cleaned.rfind(",") > cleaned.rfind(".")
        ):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        # US/international style: 1,234.50 -> 1234.50
        elif "," in cleaned and "." in cleaned:
            cleaned = cleaned.replace(",", "")
        # Thousands separator with three trailing digits: 1,234 -> 1234
        elif "," in cleaned:
            chunks = cleaned.split(",")
            if len(chunks) == 2 and len(chunks[1]) == 3:
                cleaned = "".join(chunks)
            else:
                cleaned = cleaned.replace(",", ".")

        try:
            number = float(cleaned)
        except ValueError:
            return value

        return int(number) if number.is_integer() else number

    @staticmethod
    def _normalize_date(value: Any) -> Tuple[Any, bool]:
        if value is None:
            return value, False

        if isinstance(value, (pd.Timestamp, datetime)):
            return pd.Timestamp(value).isoformat(), True

        raw = str(value).strip()
        if not raw:
            return value, False

        # Excel serial dates are interpreted only when the value is clearly
        # a serial rather than a year. Years remain untouched.
        if isinstance(value, (int, float)) and 20000 <= float(value) <= 60000:
            excel_date = pd.Timestamp("1899-12-30") + pd.to_timedelta(
                float(value),
                unit="D",
            )
            return excel_date.strftime("%Y-%m-%d"), True

        if not _DATE_LIKE_RE.match(raw):
            return value, False

        if re.match(
            r"^\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}$",
            raw,
        ):
            parts = re.split(r"[-/.]", raw)
            first, second = int(parts[0]), int(parts[1])

            if first <= 12 and second <= 12:
                # Ambiguous DD/MM vs MM/DD: do not silently invent a locale.
                return value, False

            dayfirst = first > 12
            parsed_date = pd.to_datetime(
                raw,
                dayfirst=dayfirst,
                errors="coerce",
            )
        else:
            parsed_date = pd.to_datetime(
                raw,
                errors="coerce",
            )

        if pd.isna(parsed_date):
            return value, False

        normalized_date = cast(pd.Timestamp, parsed_date)
        return normalized_date.isoformat(), True

    @classmethod
    def normalize_records(
        cls,
        records: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], List[str], Dict[str, int]]:
        """Normalize obvious locale-specific values while preserving ambiguity."""
        normalized: List[Dict[str, Any]] = []
        warnings: List[str] = []
        stats = {
            "numeric_values_normalized": 0,
            "date_values_normalized": 0,
            "ambiguous_dates_preserved": 0,
        }

        for row in records:
            out: Dict[str, Any] = {}

            for column, value in row.items():
                if cls._is_date_column(column):
                    new_value, changed = cls._normalize_date(value)
                    out[column] = new_value

                    if changed:
                        stats["date_values_normalized"] += 1
                    elif value is not None and str(value).strip():
                        raw = str(value).strip()
                        if re.match(
                            r"^\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}$",
                            raw,
                        ):
                            stats["ambiguous_dates_preserved"] += 1
                            warnings.append(
                                f"Ambiguous date preserved in column "
                                f"'{column}': '{raw}'."
                            )

                    continue

                if cls._is_numeric_column(column):
                    new_value = cls._normalize_numeric(value)
                    out[column] = new_value

                    if (
                        new_value != value
                        and isinstance(new_value, (int, float))
                    ):
                        stats["numeric_values_normalized"] += 1

                    continue

                out[column] = value

            normalized.append(out)

        # Deduplicate warnings while preserving order.
        warnings = list(dict.fromkeys(warnings))

        return normalized, warnings, stats