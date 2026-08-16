import pandas as pd
from typing import Dict, List, Tuple


class CanonicalColumnMapper:
    COLUMN_SYNONYMS: Dict[str, List[str]] = {
        "sku_id": ["sku", "sku_id", "item_code", "product_id", "item_number", "part_number"],
        "location_id": ["location", "location_id", "site_id", "warehouse", "facility", "store_id"],
        "date": ["date", "timestamp", "period", "transaction_date", "order_date", "ds"],
        "demand_qty": ["quantity", "demand", "sales", "qty", "sales_qty", "demand_qty", "units_sold"],
        "inventory_qty": ["stock", "inventory", "on_hand", "closing_balance", "stock_qty", "inventory_qty"],
        "unit_cost": ["cost", "unit_cost", "cogs", "purchase_price"],
    }

    def __init__(self, df: pd.DataFrame) -> None:
        self.df = df
        self.mapping_log: List[Dict[str, str]] = []

    def map_columns(self) -> Tuple[pd.DataFrame, Dict[str, str]]:
        renamed_cols: Dict[str, str] = {}
        original_cols = [str(col).strip() for col in self.df.columns]

        for orig in original_cols:
            clean_orig = orig.lower().replace("-", "_").replace(" ", "_")
            matched = False
            for canonical, synonyms in self.COLUMN_SYNONYMS.items():
                if clean_orig in synonyms:
                    renamed_cols[orig] = canonical
                    self.mapping_log.append({"original": orig, "canonical": canonical, "confidence": "HIGH"})
                    matched = True
                    break
            if not matched:
                renamed_cols[orig] = clean_orig

        mapped_df = self.df.rename(columns=renamed_cols)
        return mapped_df, {item["original"]: item["canonical"] for item in self.mapping_log}
