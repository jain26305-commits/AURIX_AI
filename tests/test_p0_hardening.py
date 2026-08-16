"""Unit tests for P0 hardening changes that do not require a live cloud service."""

from __future__ import annotations
from pathlib import Path

import pandas as pd
from _pytest.monkeypatch import MonkeyPatch

from aurix_core.actions.adapters import ActionExecutionAdapter
from aurix_core.actions.contracts import ActionCategory, ActionContract, ActionType, ApprovalState, ActionState
from aurix_core.config.settings import settings
from aurix_core.mlops.artifact_storage import ArtifactStorage
from aurix_core.onboarding.normalization import EnterpriseNormalizationEngine
from aurix_core.onboarding.parsers import DataParser


def _sample_action(simulate_timeout: bool = False) -> ActionContract:
    return ActionContract(
        action_id="ACT-P0-TEST",
        tenant_id="tenant-a",
        action_type=ActionType.TRIGGER_REPLENISHMENT,
        action_category=ActionCategory.EXECUTABLE,
        entity_type="inventory",
        entity_id="SKU-001",
        requested_by="user-a",
        approval_state=ApprovalState.APPROVED,
        execution_state=ActionState.APPROVED,
        approval_required=False,
        payload={"quantity": 10, "supplier_id": "SUP-1", "simulate_timeout": simulate_timeout},
        freshness_timestamp="2026-08-16T00:00:00+00:00",
        idempotency_key="IDEM-P0-TEST",
    )


def test_auth_tenant_context_is_reset_after_dependency() -> None:
    """Verify authenticated tenant context is restored after request cleanup."""
    import asyncio

    from fastapi.security import HTTPAuthorizationCredentials
    from starlette.requests import Request

    from aurix_api.security.auth import (
        create_access_token,
        get_current_tenant_context,
    )
    from aurix_core.database.tenant_context import get_current_tenant_id

    async def exercise_dependency() -> None:
        token = create_access_token(
            {
                "sub": "user-p0",
                "tenant_id": "tenant-p0",
                "roles": ["ADMIN"],
                "permissions": ["READ_DATA"],
            }
        )
        request = Request({"type": "http", "headers": []})
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token,
        )

        dependency = get_current_tenant_context(
            request,
            credentials,
            None,
        )

        context = await dependency.__anext__()
        assert context.tenant_id == "tenant-p0"
        assert get_current_tenant_id() == "tenant-p0"

        await dependency.aclose()
        assert get_current_tenant_id() is None

    asyncio.run(exercise_dependency())


def test_local_artifact_storage_round_trip(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "artifact_storage_backend", "local")
    monkeypatch.setattr(settings, "artifact_storage_path", str(tmp_path))

    payload = b"AURIX-P0-ARTIFACT"
    reference = ArtifactStorage.save_bytes(
        tenant_id="tenant-a",
        model_type="DEMAND_FORECAST",
        version="1.0.0",
        filename="champion.joblib",
        data=payload,
    )

    assert Path(reference).exists()
    assert ArtifactStorage.load_bytes(reference) == payload
    assert ArtifactStorage.verify_reference_checksum(
        reference,
        ArtifactStorage.sha256_bytes(payload),
    )


def test_locale_aware_normalization_is_conservative() -> None:
    records = [
        {
            "Req Date": "14/08/2026",
            "Unit Cost": "1.234,50",
            "Quantity": "1,234.00",
            "Ambiguous Date": "01/02/2026",
            "SKU": "SKU-001",
        }
    ]

    normalized, warnings, stats = EnterpriseNormalizationEngine.normalize_records(records)

    assert normalized[0]["Unit Cost"] == 1234.5
    assert normalized[0]["Quantity"] == 1234
    assert normalized[0]["Req Date"].startswith("2026-08-14")
    assert normalized[0]["Ambiguous Date"] == "01/02/2026"
    assert "Ambiguous date preserved" in " ".join(warnings)
    assert stats["numeric_values_normalized"] == 2


def test_xlsx_workbook_parser_discovers_all_sheets() -> None:
    from io import BytesIO

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame({"SKU": ["A"], "Quantity": [1]}).to_excel(writer, sheet_name="Demand", index=False)
        pd.DataFrame({"SKU": ["A"], "Inventory": [2]}).to_excel(writer, sheet_name="Inventory", index=False)
    workbook = DataParser.parse_xlsx_workbook(output.getvalue())

    assert [sheet[0] for sheet in workbook] == ["Demand", "Inventory"]
    assert sum(len(sheet[1]) for sheet in workbook) == 2


def test_external_idempotency_returns_same_result() -> None:
    ActionExecutionAdapter._IDEMPOTENCY_RESULTS.clear()
    action = _sample_action()

    first = ActionExecutionAdapter.execute_action("tenant-a", action)
    second = ActionExecutionAdapter.execute_action("tenant-a", action)

    assert first.external_transaction_id == second.external_transaction_id
    assert second.external_request_id == action.idempotency_key


def test_external_timeout_is_reconcilable_without_resubmission() -> None:
    ActionExecutionAdapter._IDEMPOTENCY_RESULTS.clear()
    action = _sample_action(simulate_timeout=True)

    unknown = ActionExecutionAdapter.execute_action("tenant-a", action)
    reconciled = ActionExecutionAdapter.reconcile_action("tenant-a", action)

    assert unknown.transmission_state == "EXTERNAL_UNKNOWN"
    assert reconciled.transmission_state == "VERIFIED"
    assert reconciled.external_request_id == action.idempotency_key
