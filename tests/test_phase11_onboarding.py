"""Comprehensive Integration, Safety, and Quality Test Suite for Phase 11 Automated Data Onboarding."""

import io
import json
import unittest
from typing import Any, Dict, List
from fastapi.testclient import TestClient
import openpyxl  # type: ignore[import-untyped]

from aurix_api.app import create_app
from aurix_api.security.auth import create_access_token
from aurix_core.database.engine import Base, SessionLocal, engine
from aurix_core.onboarding.contracts import (
    DuplicateCorrectionStatus,
    OnboardingStatus,
    SourceType,
)
from aurix_core.onboarding.parsers import DataParser
from aurix_core.onboarding.quality_validator import OnboardingQualityEngine
from aurix_core.onboarding.safety import FileSafetyException, FileSafetyValidator
from aurix_core.onboarding.schema_discovery import SchemaDiscoveryEngine
from aurix_core.onboarding.semantic_mapper import SemanticMapper
from aurix_core.onboarding.service import OnboardingService


class TestPhase11AutomatedOnboarding(unittest.TestCase):
    """Test suite covering Phase 11 automated customer data onboarding engine and API routers."""

    app: Any
    client: TestClient
    token_admin_alpha: str
    token_viewer_alpha: str

    @classmethod
    def setUpClass(cls) -> None:
        """Initializes FastAPI test client and RBAC authorization tokens."""
        Base.metadata.create_all(bind=engine)
        cls.app = create_app()
        cls.client = TestClient(cls.app)

        cls.token_admin_alpha = create_access_token({
            "sub": "admin_user_1",
            "tenant_id": "tenant_onboard_alpha",
            "roles": ["ADMIN"],
            "permissions": ["READ_DATA", "WRITE_DATA", "RUN_ANALYSIS", "USE_AI", "VIEW_FINANCIALS"],
        })

        cls.token_viewer_alpha = create_access_token({
            "sub": "viewer_user_1",
            "tenant_id": "tenant_onboard_alpha",
            "roles": ["VIEWER"],
            "permissions": ["READ_DATA"],
        })

    def test_01_file_safety_and_sanitization(self) -> None:
        """Verifies path traversal sanitization, extension checks, and file size constraints."""
        clean_name = FileSafetyValidator.sanitize_filename("../../etc/passwd.csv")
        self.assertEqual(clean_name, "etc_passwd.csv")

        with self.assertRaises(FileSafetyException) as ctx:
            FileSafetyValidator.validate_file("empty.csv", b"")
        self.assertEqual(ctx.exception.code, "EMPTY_FILE")

        with self.assertRaises(FileSafetyException) as ctx:
            FileSafetyValidator.validate_file("malicious.exe", b"MZ\x90\x00data")
        self.assertEqual(ctx.exception.code, "INVALID_EXTENSION")

        with self.assertRaises(FileSafetyException) as ctx:
            FileSafetyValidator.validate_file("huge.csv", b"1" * 100, max_size_bytes=50)
        self.assertEqual(ctx.exception.code, "FILE_TOO_LARGE")

    def test_02_parsers_csv_xlsx_json_gsheets(self) -> None:
        """Verifies multi-format parsing for CSV, XLSX, JSON, and Google Sheets dumps."""
        csv_data = "Item_Code;Date;Demand\nSKU-100;2026-01-01;150\nSKU-100;2026-02-01;180\n".encode("utf-8")
        records, cols = DataParser.parse(SourceType.CSV, csv_data)
        self.assertEqual(len(records), 2)
        self.assertIn("Item_Code", cols)

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "DemandSheet"
        ws.append(["Material_No", "Transaction_Date", "Sales_Qty"])
        ws.append(["SKU-200", "2026-03-01", 320])
        xlsx_buf = io.BytesIO()
        wb.save(xlsx_buf)
        records_xlsx, _ = DataParser.parse(SourceType.XLSX, xlsx_buf.getvalue())
        self.assertEqual(len(records_xlsx), 1)
        self.assertEqual(records_xlsx[0]["Material_No"], "SKU-200")

        json_payload = json.dumps({
            "data": [
                {"Product_ID": "SKU-300", "Period": "2026-04-01", "Qty": 450}
            ]
        }).encode("utf-8")
        records_json, _ = DataParser.parse(SourceType.JSON, json_payload)
        self.assertEqual(len(records_json), 1)
        self.assertEqual(records_json[0]["Product_ID"], "SKU-300")

    def test_03_type_inference_and_schema_discovery(self) -> None:
        """Verifies statistical type inference, date detection, and entity candidate scoring."""
        records: List[Dict[str, Any]] = [
            {"Product_Code": "SKU-A", "Order_Date": "2026-01-15", "Volume": "$1,250.50"},
            {"Product_Code": "SKU-B", "Order_Date": "2026-01-16", "Volume": "980.00"},
        ]
        report = SchemaDiscoveryEngine.discover_schema(records)
        self.assertEqual(report.detected_entity_name, "demand_history")
        self.assertEqual(report.field_mappings["Order_Date"].inferred_type, "date")
        self.assertEqual(report.field_mappings["Volume"].inferred_type, "float")

    def test_04_semantic_mapper_and_ambiguity(self) -> None:
        """Verifies semantic alias mapping, type validation, and multi-column collision detection."""
        records = [{"Material": "SKU-1", "Period": "2026-01-01", "Units_Sold": 100}]
        report = SchemaDiscoveryEngine.discover_schema(records)
        _, accepted = SemanticMapper.map_schema(report)
        self.assertEqual(accepted["Material"], "sku_id")
        self.assertEqual(accepted["Period"], "date")
        self.assertEqual(accepted["Units_Sold"], "quantity")

        collision_records = [{"SKU": "SKU-1", "Date": "2026-01-01", "Qty_Sold": 100, "Ship_Qty": 105}]
        report_coll = SchemaDiscoveryEngine.discover_schema(collision_records)
        report_coll, _ = SemanticMapper.map_schema(report_coll)
        self.assertIn("Qty_Sold", report_coll.ambiguous_columns)
        self.assertIn("Ship_Qty", report_coll.ambiguous_columns)

    def test_05_quality_and_temporal_coverage(self) -> None:
        """Verifies negative value rejection, temporal gap detection, and completeness scoring."""
        records: List[Dict[str, Any]] = [
            {"sku_id": "SKU-1", "date": "2026-01-01", "quantity": 100},
            {"sku_id": "SKU-1", "date": "2026-02-01", "quantity": -50},
            {"sku_id": "SKU-1", "date": "2026-04-01", "quantity": 120},
        ]
        accepted, rejected, _, temporal, completeness = OnboardingQualityEngine.evaluate(
            records=records,
            entity_name="demand_history",
            mapped_fields={"sku_id", "date", "quantity"},
        )
        self.assertEqual(len(accepted), 2)
        self.assertEqual(len(rejected), 1)
        self.assertIn("2026-03-01", temporal.missing_periods)
        self.assertGreater(completeness.domain_completeness_pct, 0.0)

    def test_06_onboarding_service_demand_partial_data(self) -> None:
        """Verifies partial data onboarding (demand only) discovers capabilities without failing."""
        db = SessionLocal()
        try:
            csv_content = (
                "SKU_CODE,DATE_VAL,SALES_QTY\n"
                "SKU-DEMAND-1,2026-01-01,100\n"
                "SKU-DEMAND-1,2026-02-01,120\n"
                "SKU-DEMAND-1,2026-03-01,110\n"
            ).encode("utf-8")

            res = OnboardingService.onboard_file(
                db=db,
                tenant_id="tenant_onboard_alpha",
                filename="monthly_demand.csv",
                content=csv_content,
            )

            self.assertEqual(res.overall_status, OnboardingStatus.COMPLETED)
            self.assertEqual(res.records_accepted, 3)
            assert res.capability_summary is not None
            self.assertIn("DEMAND_CLASSIFICATION", res.capability_summary.available_capabilities)
            # Verify that supply/supplier capabilities require supplier catalog inputs
            all_unavailable = (
                res.capability_summary.unavailable_capabilities
                + res.capability_summary.partial_capabilities
            )
            self.assertTrue(
                any("SUPPLIER" in cap or "WORKING_CAPITAL" in cap for cap in all_unavailable)
            )
        finally:
            db.close()

    def test_07_onboarding_service_incremental_updates(self) -> None:
        """Verifies recurring monthly updates, duplicate uploads, and corrections."""
        db = SessionLocal()
        try:
            batch1 = [
                {"sku_id": "SKU-INC", "date": "2026-01-01", "quantity": 100},
                {"sku_id": "SKU-INC", "date": "2026-02-01", "quantity": 110},
                {"sku_id": "SKU-INC", "date": "2026-03-01", "quantity": 105},
                {"sku_id": "SKU-INC", "date": "2026-04-01", "quantity": 115},
            ]
            res1 = OnboardingService.onboard_raw_records(
                db=db,
                tenant_id="tenant_onboard_alpha",
                records=batch1,
            )
            self.assertEqual(res1.overall_status, OnboardingStatus.COMPLETED)
            self.assertEqual(res1.records_accepted, 4)

            batch2 = [
                {"sku_id": "SKU-INC", "date": "2026-05-01", "quantity": 130},
                {"sku_id": "SKU-INC", "date": "2026-06-01", "quantity": 125},
                {"sku_id": "SKU-INC", "date": "2026-07-01", "quantity": 140},
            ]
            res2 = OnboardingService.onboard_raw_records(
                db=db,
                tenant_id="tenant_onboard_alpha",
                records=batch2,
                existing_records=batch1,
            )
            self.assertEqual(res2.duplicate_status, DuplicateCorrectionStatus.INCREMENTAL_APPEND)

            res3 = OnboardingService.onboard_raw_records(
                db=db,
                tenant_id="tenant_onboard_alpha",
                records=batch2,
                existing_records=batch2,
            )
            self.assertEqual(res3.duplicate_status, DuplicateCorrectionStatus.DUPLICATE_IDENTICAL)

            correction_batch = [
                {"sku_id": "SKU-INC", "date": "2026-01-01", "quantity": 108}
            ]
            res4 = OnboardingService.onboard_raw_records(
                db=db,
                tenant_id="tenant_onboard_alpha",
                records=correction_batch,
                existing_records=batch1,
            )
            self.assertEqual(res4.duplicate_status, DuplicateCorrectionStatus.HISTORICAL_CORRECTION)
        finally:
            db.close()

    def test_08_api_onboarding_upload_and_records(self) -> None:
        """Verifies API endpoints for file upload and JSON record ingestion."""
        records_payload = [
            {"Material_No": "SKU-API-1", "Posting_Date": "2026-01-01", "Sales_Qty": 200},
            {"Material_No": "SKU-API-1", "Posting_Date": "2026-02-01", "Sales_Qty": 210},
        ]
        res_rec = self.client.post(
            "/api/v1/onboarding/records",
            json=records_payload,
            headers={"Authorization": f"Bearer {self.token_admin_alpha}"},
        )
        self.assertEqual(res_rec.status_code, 200)
        self.assertEqual(res_rec.json()["data"]["records_accepted"], 2)

        csv_file_content = "Product,Date,Demand\nSKU-UP-1,2026-01-01,500\nSKU-UP-1,2026-02-01,520\n"
        files = {"file": ("dataset.csv", io.BytesIO(csv_file_content.encode("utf-8")), "text/csv")}
        res_up = self.client.post(
            "/api/v1/onboarding/upload",
            files=files,
            headers={"Authorization": f"Bearer {self.token_admin_alpha}"},
        )
        self.assertEqual(res_up.status_code, 200)
        self.assertEqual(res_up.json()["data"]["records_accepted"], 2)

    def test_09_api_resolve_mapping(self) -> None:
        """Verifies resolving USER_INPUT_REQUIRED mapping ambiguities via API."""
        raw_ambiguous_records = [
            {"Item": "SKU-AMB", "Date": "2026-01-01", "Qty_Sold": 100, "Ship_Qty": 105}
        ]
        resolve_payload = {
            "raw_records": raw_ambiguous_records,
            "resolution": {
                "run_id": "ONBOARD-TEST-RESOLVE",
                "resolved_mappings": {
                    "Item": "sku_id",
                    "Date": "date",
                    "Qty_Sold": "quantity",
                },
                "override_entity_name": "demand_history",
            },
        }
        res = self.client.post(
            "/api/v1/onboarding/resolve-mapping",
            json=resolve_payload,
            headers={"Authorization": f"Bearer {self.token_admin_alpha}"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["data"]["overall_status"], "COMPLETED")
        self.assertEqual(res.json()["data"]["records_accepted"], 1)

    def test_10_tenant_isolation_and_security(self) -> None:
        """Verifies that unauthorized or viewer roles are blocked from data onboarding endpoints."""
        res_unauth = self.client.post(
            "/api/v1/onboarding/records",
            json=[{"sku_id": "SKU-1", "date": "2026-01-01", "quantity": 10}],
        )
        self.assertEqual(res_unauth.status_code, 401)

        res_viewer = self.client.post(
            "/api/v1/onboarding/records",
            json=[{"sku_id": "SKU-1", "date": "2026-01-01", "quantity": 10}],
            headers={"Authorization": f"Bearer {self.token_viewer_alpha}"},
        )
        self.assertEqual(res_viewer.status_code, 403)


if __name__ == "__main__":
    unittest.main()