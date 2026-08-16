from enum import Enum
from typing import Dict, Any, cast
from datetime import datetime
from pydantic import BaseModel, Field


class FieldStatus(str, Enum):
    REQUIRED = "REQUIRED"
    OPTIONAL = "OPTIONAL"
    DOMAIN_SPECIFIC = "DOMAIN_SPECIFIC"
    DERIVED = "DERIVED"
    INFERRED = "INFERRED"
    USER_PROVIDED = "USER_PROVIDED"
    ASSUMPTION = "ASSUMPTION"
    UNAVAILABLE = "UNAVAILABLE"


class DataCategory(str, Enum):
    OBSERVED = "OBSERVED"
    DERIVED = "DERIVED"
    INFERRED = "INFERRED"
    USER_INPUT = "USER_INPUT"
    ASSUMPTION = "ASSUMPTION"
    MODEL_OUTPUT = "MODEL_OUTPUT"


class CanonicalRecord(BaseModel):
    entity_id: str = Field(
        ...,
        description="Unique SKU / Product Identifier",
        json_schema_extra={"status": FieldStatus.REQUIRED, "category": DataCategory.OBSERVED},
    )
    location_id: str = Field(
        ...,
        description="Node / Facility Identifier",
        json_schema_extra={"status": FieldStatus.REQUIRED, "category": DataCategory.OBSERVED},
    )
    timestamp: datetime = Field(
        ...,
        description="Observation Timestamp",
        json_schema_extra={"status": FieldStatus.REQUIRED, "category": DataCategory.OBSERVED},
    )
    quantity: float = Field(
        ...,
        description="Observed transaction/demand quantity",
        json_schema_extra={"status": FieldStatus.REQUIRED, "category": DataCategory.OBSERVED},
    )

    is_negative_adjusted: bool = Field(
        False, json_schema_extra={"status": FieldStatus.DERIVED, "category": DataCategory.DERIVED}
    )

    domain_attributes: Dict[str, Dict[str, Any]] = Field(
        default_factory=lambda: cast(
            Dict[str, Dict[str, Any]],
            {
                "eda": {},
                "demand": {},
                "forecasting": {},
                "inventory": {},
                "supply": {},
                "lead_time": {},
                "logistics": {},
                "network": {},
                "finance": {},
                "scenarios": {},
                "ai": {},
            },
        ),
        description="Namespaced extensions for future domain expansion",
    )

    class Config:
        use_enum_values = True
