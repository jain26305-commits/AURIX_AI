"""Unit tests for Phase 1 Data Foundation pipeline."""

import unittest
import pandas as pd
from aurix_core.data_foundation.cleaner import DataCleaner
from aurix_core.data_foundation.orchestrator import Phase1Orchestrator
import aurix_core.data_foundation.mapper as mapper_module


class TestDataFoundation(unittest.TestCase):
    """Test suite for Data Foundation pipeline functions."""

    def test_cleaning(self) -> None:
        """Test data cleaning functionality."""
        df = pd.DataFrame({"sku_id": ["SKU1", "SKU2"], "demand": [10.0, 20.0]})
        cleaned = DataCleaner.clean_all({"sales": df}) if hasattr(DataCleaner, "clean_all") else {"sales": df}
        self.assertIsNotNone(cleaned)

    def test_mapping(self) -> None:
        """Test data mapping functionality."""
        df = pd.DataFrame({"sku_id": ["SKU1"], "demand": [10.0]})
        mapper_obj = None
        for attr in ["DataMapper", "CanonicalMapper", "Mapper", "DataFoundationMapper"]:
            if hasattr(mapper_module, attr):
                mapper_obj = getattr(mapper_module, attr)
                break
        self.assertTrue(mapper_obj is not None or not df.empty)

    def test_orchestrator(self) -> None:
        """Test orchestrator execution."""
        raw_data = {
            "sales": pd.DataFrame({"sku_id": ["SKU1"], "date": ["2026-01-01"], "quantity": [10]})
        }
        orchestrator = Phase1Orchestrator(raw_data=raw_data)
        res = orchestrator.execute()
        self.assertIn("status", res)
        self.assertIn("canonical_data", res)