"""Controlled Phase 14 action execution adapter with timeout handling."""

import logging
import uuid
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from aurix_core.actions.contracts import ActionContract, ActionType

logger = logging.getLogger("aurix_core.actions.adapters")


class ExternalExecutionResult(BaseModel):
    """Normalized response container capturing external system execution results and transmission states."""

    success: bool = False
    external_transaction_id: Optional[str] = None
    external_record_id: Optional[str] = None
    status_code: str = "PENDING"

    # Possible states:
    # EXECUTION_SENT
    # EXTERNAL_ACCEPTED
    # VERIFICATION_PENDING
    # VERIFIED
    # EXTERNAL_UNKNOWN
    # EXTERNAL_REJECTED
    # DRY_RUN_SUCCESS
    transmission_state: str = "PENDING"

    response_payload: Dict[str, Any] = Field(
        default_factory=dict
    )

    error_message: Optional[str] = None


class ActionExecutionAdapter:
    """Manages controlled execution of operational writes through Phase 12 connectors with timeout/unknown resilience."""

    @classmethod
    def execute_action(
        cls,
        tenant_id: str,
        action: ActionContract,
        dry_run: bool = False,
    ) -> ExternalExecutionResult:
        """
        Executes an approved operational action via the appropriate Phase 12 connector adapter.

        Supports:
        - dry-run simulation
        - idempotent request transmission
        - simulated network timeout / unknown outcomes
        - explicit separation between transmission and verification
        """
        logger.info(
            "Executing action [ID: %s, Type: %s, Tenant: %s, DryRun: %s]",
            action.action_id,
            action.action_type,
            tenant_id,
            dry_run,
        )

        # ---------------------------------------------------------
        # 1. Simulated network timeout / unknown outcome
        # ---------------------------------------------------------
        if action.payload.get("simulate_timeout", False):
            return ExternalExecutionResult(
                success=False,
                status_code="TIMEOUT_504",
                transmission_state="EXTERNAL_UNKNOWN",
                error_message=(
                    "Network timeout occurred after request "
                    "transmission. External transaction state "
                    "is unknown."
                ),
            )

        # ---------------------------------------------------------
        # 2. Dry-run mode
        # ---------------------------------------------------------
        #
        # Dry-run is explicitly NOT an executed external action.
        # It therefore never returns VERIFIED.
        #
        if dry_run:
            return ExternalExecutionResult(
                success=True,
                external_transaction_id=(
                    f"DRYRUN-TX-"
                    f"{uuid.uuid4().hex[:8].upper()}"
                ),
                external_record_id=(
                    f"DRYRUN-REC-{action.entity_id}"
                ),
                status_code="DRY_RUN_SUCCESS",
                transmission_state="DRY_RUN_SUCCESS",
                response_payload={
                    "message": (
                        "Preflight validation passed. "
                        "External write simulated successfully."
                    )
                },
            )

        # ---------------------------------------------------------
        # 3. Route by action type
        # ---------------------------------------------------------
        try:
            if action.action_type == ActionType.TRANSFER_STOCK:
                return cls._execute_stock_transfer(
                    tenant_id,
                    action,
                )

            if action.action_type == ActionType.TRIGGER_REPLENISHMENT:
                return cls._execute_replenishment(
                    tenant_id,
                    action,
                )

            return ExternalExecutionResult(
                success=False,
                status_code="UNSUPPORTED_ACTION_TYPE",
                transmission_state="EXTERNAL_REJECTED",
                error_message=(
                    f"Action type '{action.action_type}' "
                    "does not have a verified execution adapter."
                ),
            )

        except Exception as exc:
            logger.error(
                "External execution adapter failure for action %s: %s",
                action.action_id,
                str(exc),
                exc_info=True,
            )

            return ExternalExecutionResult(
                success=False,
                status_code="ADAPTER_EXCEPTION",
                transmission_state="EXTERNAL_UNKNOWN",
                error_message=str(exc),
            )

    @classmethod
    def _execute_stock_transfer(
        cls,
        tenant_id: str,
        action: ActionContract,
    ) -> ExternalExecutionResult:
        """
        Executes stock transfer via the Generic WMS connector boundary.

        Current implementation is a controlled execution/test-double
        boundary. A successful simulated transaction includes simulated
        authoritative verification, therefore transmission_state is
        VERIFIED.

        A future live WMS implementation may instead return
        VERIFICATION_PENDING until a separate external verification call
        confirms the resulting warehouse state.
        """
        payload = action.payload

        source_location = payload.get(
            "source_location",
            "WH-MAIN",
        )

        dest_location = payload.get(
            "destination_location",
            "WH-RETAIL",
        )

        sku_id = action.entity_id

        quantity = payload.get(
            "quantity",
            1.0,
        )

        transfer_body = {
            "idempotency_key": action.idempotency_key,
            "sku_id": sku_id,
            "quantity": quantity,
            "source_location": source_location,
            "destination_location": dest_location,
            "reference": action.action_id,
        }

        tx_id = (
            f"TX-WMS-"
            f"{uuid.uuid4().hex[:8].upper()}"
        )

        rec_id = (
            f"TRF-"
            f"{uuid.uuid4().hex[:6].upper()}"
        )

        logger.info(
            "Stock transfer transmitted and "
            "authoritatively verified via WMS execution boundary "
            "[TxID: %s]",
            tx_id,
        )

        return ExternalExecutionResult(
            success=True,
            external_transaction_id=tx_id,
            external_record_id=rec_id,
            status_code="VERIFIED_200",
            transmission_state="VERIFIED",
            response_payload={
                **transfer_body,
                "verification": {
                    "status": "VERIFIED",
                    "verification_source": "WMS_EXECUTION_DOUBLE",
                    "transaction_id": tx_id,
                },
            },
        )

    @classmethod
    def _execute_replenishment(
        cls,
        tenant_id: str,
        action: ActionContract,
    ) -> ExternalExecutionResult:
        """
        Triggers procurement replenishment via the Odoo ERP connector boundary.

        Current implementation is a controlled execution/test-double
        boundary. A successful simulated transaction includes simulated
        authoritative verification, therefore transmission_state is
        VERIFIED.

        A future live ERP implementation may return
        VERIFICATION_PENDING until external ERP confirmation is obtained.
        """
        payload = action.payload

        sku_id = action.entity_id

        quantity = payload.get(
            "quantity",
            100.0,
        )

        supplier_id = payload.get(
            "supplier_id",
            "SUP-DEFAULT",
        )

        po_body = {
            "idempotency_key": action.idempotency_key,
            "product_code": sku_id,
            "order_qty": quantity,
            "partner_id": supplier_id,
            "origin": action.action_id,
        }

        tx_id = (
            f"TX-ERP-"
            f"{uuid.uuid4().hex[:8].upper()}"
        )

        rec_id = (
            f"PO-"
            f"{uuid.uuid4().hex[:6].upper()}"
        )

        logger.info(
            "Replenishment purchase order transmitted and "
            "authoritatively verified via ERP execution boundary "
            "[TxID: %s]",
            tx_id,
        )

        return ExternalExecutionResult(
            success=True,
            external_transaction_id=tx_id,
            external_record_id=rec_id,
            status_code="VERIFIED_200",
            transmission_state="VERIFIED",
            response_payload={
                **po_body,
                "verification": {
                    "status": "VERIFIED",
                    "verification_source": "ERP_EXECUTION_DOUBLE",
                    "transaction_id": tx_id,
                },
            },
        )