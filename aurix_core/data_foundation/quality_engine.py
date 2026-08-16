"""Data Quality Engine for operational supply chain ingestion."""

from typing import Any, Dict, List
import pandas as pd


class DataQualityEngine:
    """
    Validates operational datasets before entering the Canonical Database.
    Distinguishes between ERROR (blocks ingestion) and WARNING (persisted but flagged).
    Strictly follows Zero-Fabrication principles.
    """

    @staticmethod
    def validate(df: pd.DataFrame, domain: str) -> Dict[str, Any]:
        """Runs quality rules against the dataframe based on its target domain."""
        errors: List[str] = []
        warnings: List[str] = []

        if df.empty:
            errors.append(f"Dataset for domain '{domain}' is empty.")
            return {"status": "ERROR", "errors": errors, "warnings": warnings}

        # Validate mandatory schema requirements
        required_columns = []
        if domain == "inventory":
            required_columns = ["sku_id", "location_id"]
        elif domain == "products":
            required_columns = ["sku_code"]
        elif domain == "locations":
            required_columns = ["location_id"]
        elif domain == "suppliers":
            required_columns = ["supplier_id"]

        for col in required_columns:
            if col not in df.columns:
                errors.append(f"Missing required column: {col}")

        # Domain-specific business constraints
        if domain == "inventory":
            if "on_hand" in df.columns and (df["on_hand"] < 0).any():
                errors.append("Negative inventory quantities are strictly prohibited.")

        if domain == "suppliers":
            if "lead_time_days" in df.columns and (df["lead_time_days"] < 0).any():
                errors.append("Supplier lead time cannot be negative.")

        # Resolve validation state
        if errors:
            status = "ERROR"
        elif warnings:
            status = "WARNING"
        else:
            status = "VALIDATED"

        return {"status": status, "errors": errors, "warnings": warnings}