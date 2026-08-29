"""Data Quality Engine for operational supply chain & Phase 19 Canonical Data Fabric."""

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

        # Mandatory schema requirements across all Phase 19 entities
        required_columns = []
        dom = domain.lower().strip()
        if dom in ("inventory", "inventory_positions"):
            required_columns = ["sku_id", "location_id"]
        elif dom in ("products", "skus"):
            required_columns = ["sku_code"]
        elif dom in ("locations", "warehouses"):
            required_columns = ["location_id"]
        elif dom in ("suppliers", "vendors"):
            required_columns = ["supplier_id"]
        elif dom in ("orders", "sales_orders"):
            required_columns = ["order_number", "total_amount"]
        elif dom in ("purchase_orders", "pos"):
            required_columns = ["po_number", "supplier_id"]
        elif dom in ("invoices", "bills"):
            required_columns = ["invoice_number", "total_amount"]

        for col in required_columns:
            if col not in df.columns:
                errors.append(f"Missing required column: {col}")

        # Business Constraint Assertions
        if dom in ("inventory", "inventory_positions"):
            if "on_hand" in df.columns and (df["on_hand"] < 0).any():
                errors.append("Negative inventory quantities are strictly prohibited.")

        if dom in ("suppliers", "vendors"):
            if "lead_time_days" in df.columns and (df["lead_time_days"] < 0).any():
                errors.append("Supplier lead time cannot be negative.")

        if dom in ("orders", "invoices", "purchase_orders"):
            if "total_amount" in df.columns and (df["total_amount"] < 0).any():
                errors.append("Transaction total amount cannot be negative.")

        if errors:
            status = "ERROR"
        elif warnings:
            status = "WARNING"
        else:
            status = "VALIDATED"

        return {"status": status, "errors": errors, "warnings": warnings}
