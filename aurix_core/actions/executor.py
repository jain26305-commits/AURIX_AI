"""Master Action Execution Engine, State Machine, and Orchestrator for Phase 14 (Corrective Hardening v14.1)."""

import hashlib
import json
import logging
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel
from sqlalchemy.orm import Session

from aurix_core.actions.adapters import ActionExecutionAdapter, ExternalExecutionResult
from aurix_core.actions.contracts import (
    ActionAuditRecord,
    ActionCategory,
    ActionContract,
    ActionState,
    ActionType,
    ApprovalState,
)
from aurix_core.actions.policy import ActionPolicyEngine, PolicyEvaluationResult
from aurix_core.events.contracts import EventTaxonomy, InternalEvent
from aurix_core.events.processor import EventProcessor

logger = logging.getLogger("aurix_core.actions.executor")


class ActionExecutionResult(BaseModel):
    """Master result envelope for action orchestration operations."""
    action_id: str
    tenant_id: str
    execution_state: ActionState
    approval_state: ApprovalState
    success: bool = False
    message: str = ""
    external_transaction_id: Optional[str] = None
    error_message: Optional[str] = None


class ActionExecutor:
    """Coordinates action validation, policy checks, approvals, execution adapters, and Phase 13 events under hardening rules."""

    _lock = threading.Lock()
    _ACTIONS_STORE: Dict[str, Dict[str, ActionContract]] = {}
    _AUDIT_STORE: Dict[str, List[ActionAuditRecord]] = {}

    @classmethod
    def _compute_action_hash(cls, action: ActionContract) -> str:
        """Computes a deterministic content hash of the action payload and core attributes for immutability validation."""
        canonical_data = {
            "action_type": action.action_type.value,
            "action_category": action.action_category.value,
            "entity_type": action.entity_type,
            "entity_id": action.entity_id,
            "payload": action.payload,
        }
        serialized = json.dumps(canonical_data, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @classmethod
    def create_action(
        cls,
        tenant_id: str,
        action_type: ActionType,
        action_category: ActionCategory,
        entity_type: str,
        entity_id: str,
        requested_by: str,
        payload: Dict[str, Any],
        recommendation_id: Optional[str] = None,
        source_run_id: Optional[str] = None,
        capability_name: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> ActionContract:
        """Creates a new operational action contract in CREATED state with idempotency key generation."""
        action_id = f"ACT-{uuid.uuid4().hex[:8].upper()}"
        idempotency_hash = uuid.uuid5(
            uuid.NAMESPACE_DNS,
            f"{tenant_id}:{action_id}",
        ).hex
        idempotency_key = f"IDEM-{idempotency_hash[:20]}"
        action = ActionContract(
            action_id=action_id,
            tenant_id=tenant_id,
            action_type=action_type,
            action_category=action_category,
            entity_type=entity_type,
            entity_id=entity_id,
            recommendation_id=recommendation_id,
            source_run_id=source_run_id,
            capability_name=capability_name,
            requested_by=requested_by,
            approval_required=action_category in (ActionCategory.APPROVAL_REQUIRED, ActionCategory.EXECUTABLE),
            approval_state=ApprovalState.PENDING,
            execution_state=ActionState.CREATED,
            payload=payload,
            freshness_timestamp=datetime.now(timezone.utc).isoformat(),
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )

        with cls._lock:
            tenant_actions = cls._ACTIONS_STORE.setdefault(tenant_id, {})
            tenant_actions[action_id] = action

        cls._record_audit(
            tenant_id=tenant_id,
            action_id=action_id,
            actor_id=requested_by,
            actor_role="SYSTEM",
            prev_state=None,
            new_state=ActionState.CREATED,
            metadata={"action_type": action_type.value},
        )
        return action

    @classmethod
    def preflight_action(
        cls,
        db: Session,
        tenant_id: str,
        action_id: str,
        actor_id: str,
        actor_roles: List[str],
    ) -> Tuple[bool, Optional[str], Optional[PolicyEvaluationResult]]:
        """
        Performs preflight validation, freshness check, conflict check, and policy evaluation.
        Transitions action from CREATED -> VALIDATING -> VALIDATED or REJECTED / ACTION_CONFLICT.
        """
        action = cls._get_action_or_raise(tenant_id, action_id)
        cls._transition_state(tenant_id, action, ActionState.VALIDATING, actor_id, actor_roles)

        with cls._lock:
            tenant_actions = list(cls._ACTIONS_STORE.get(tenant_id, {}).values())

        policy_res: PolicyEvaluationResult = ActionPolicyEngine.evaluate_policy(
            action, actor_id, actor_roles, active_tenant_actions=tenant_actions
        )

        action.approval_required = policy_res.requires_approval

        if not policy_res.is_allowed:
            conflict_detected = "conflicting_action_id" in policy_res.evaluated_rules
            target_state = ActionState.ACTION_CONFLICT if conflict_detected else ActionState.REJECTED
            cls._transition_state(
                tenant_id, action, target_state, actor_id, actor_roles, {"reason": policy_res.block_reason}
            )
            action.error_message = policy_res.block_reason
            return False, policy_res.block_reason, policy_res

        if policy_res.requires_approval:
            cls._transition_state(
                tenant_id, action, ActionState.PENDING_APPROVAL, actor_id, actor_roles, {"policy": policy_res.evaluated_rules}
            )
            return True, "Action requires human approval before execution.", policy_res

        cls._transition_state(tenant_id, action, ActionState.VALIDATED, actor_id, actor_roles)
        return True, "Preflight validation passed successfully.", policy_res

    @classmethod
    def approve_action(
        cls,
        db: Session,
        tenant_id: str,
        action_id: str,
        approver_id: str,
        approver_role: str,
        comments: Optional[str] = None,
    ) -> ActionContract:
        """Grants human approval for an action in PENDING_APPROVAL state and captures an immutability approval hash."""
        action = cls._get_action_or_raise(tenant_id, action_id)
        if action.execution_state != ActionState.PENDING_APPROVAL:
            raise ValueError(f"Action {action_id} is not pending approval (Current state: {action.execution_state}).")

        if action.requested_by == approver_id and "ADMIN" not in [approver_role.upper()]:
            raise ValueError("Segregation of duties violation: Requesting user cannot approve their own action.")

        action.approval_state = ApprovalState.APPROVED
        action.approval_hash = cls._compute_action_hash(action)

        cls._transition_state(
            tenant_id,
            action,
            ActionState.APPROVED,
            approver_id,
            [approver_role],
            {"comments": comments, "approval_hash": action.approval_hash},
        )

        cls._emit_phase13_event(db, tenant_id, action, EventTaxonomy.SCENARIO_UPDATED, "ACTION_APPROVED")
        return action

    @classmethod
    def reject_action(
        cls,
        db: Session,
        tenant_id: str,
        action_id: str,
        approver_id: str,
        approver_role: str,
        comments: Optional[str] = None,
    ) -> ActionContract:
        """Rejects an action in PENDING_APPROVAL state."""
        action = cls._get_action_or_raise(tenant_id, action_id)
        if action.execution_state != ActionState.PENDING_APPROVAL:
            raise ValueError(f"Action {action_id} cannot be rejected in state {action.execution_state}.")

        action.approval_state = ApprovalState.REJECTED
        cls._transition_state(
            tenant_id, action, ActionState.REJECTED, approver_id, [approver_role], {"comments": comments}
        )
        return action

    @classmethod
    def execute_action(
        cls,
        db: Session,
        tenant_id: str,
        action_id: str,
        executor_id: str,
        executor_roles: List[str],
        dry_run: bool = False,
    ) -> ActionExecutionResult:
        """
        Executes an approved or validated action via Phase 12 execution adapter.
        Enforces strict separation: EXTERNAL_ACCEPTED != VERIFIED.
        """
        action = cls._get_action_or_raise(tenant_id, action_id)

        if action.approval_required:
            if action.approval_state != ApprovalState.APPROVED:
                return ActionExecutionResult(
                    action_id=action_id,
                    tenant_id=tenant_id,
                    execution_state=action.execution_state,
                    approval_state=action.approval_state,
                    success=False,
                    message="Action execution blocked: Human approval has not been granted.",
                )

            current_hash = cls._compute_action_hash(action)
            if action.approval_hash and current_hash != action.approval_hash:
                action.approval_state = ApprovalState.INVALIDATED
                cls._transition_state(
                    tenant_id,
                    action,
                    ActionState.APPROVAL_INVALIDATED,
                    executor_id,
                    executor_roles,
                    {"reason": "Payload mutated post-approval"},
                )
                return ActionExecutionResult(
                    action_id=action_id,
                    tenant_id=tenant_id,
                    execution_state=ActionState.APPROVAL_INVALIDATED,
                    approval_state=action.approval_state,
                    success=False,
                    message="Action execution blocked: Action payload was modified after approval. Approval invalidated.",
                )

        if action.execution_state not in (ActionState.VALIDATED, ActionState.APPROVED):
            return ActionExecutionResult(
                action_id=action_id,
                tenant_id=tenant_id,
                execution_state=action.execution_state,
                approval_state=action.approval_state,
                success=False,
                message=f"Action cannot execute from state {action.execution_state}.",
            )

        cls._transition_state(tenant_id, action, ActionState.EXECUTION_SENT, executor_id, executor_roles)

        try:
            exec_res: ExternalExecutionResult = ActionExecutionAdapter.execute_action(
                tenant_id, action, dry_run=dry_run
            )
        except Exception as e:
            logger.error("Unhandled adapter crash for action %s: %s", action_id, str(e), exc_info=True)
            exec_res = ExternalExecutionResult(
                success=False,
                status_code="ADAPTER_CRASH",
                transmission_state="EXTERNAL_UNKNOWN",
                error_message=f"Adapter execution crashed: {str(e)}",
            )

        action.actual_result = exec_res.response_payload
        action.external_transaction_id = exec_res.external_transaction_id
        action.external_request_id = exec_res.external_request_id or action.idempotency_key

        if exec_res.transmission_state == "EXTERNAL_UNKNOWN" or not exec_res.success:
            target_state = ActionState.EXTERNAL_UNKNOWN if exec_res.transmission_state == "EXTERNAL_UNKNOWN" else ActionState.COMPENSATION_REQUIRED
            if dry_run:
                target_state = ActionState.FAILED

            cls._transition_state(
                tenant_id, action, target_state, executor_id, executor_roles, {"error": exec_res.error_message}
            )
            action.error_message = exec_res.error_message
            return ActionExecutionResult(
                action_id=action_id,
                tenant_id=tenant_id,
                execution_state=target_state,
                approval_state=action.approval_state,
                success=False,
                message="External execution resulted in an unknown state (timeout or unconfirmed transmission). Manual verification required.",
                error_message=exec_res.error_message,
            )

        # Transmission accepted
        cls._transition_state(
            tenant_id,
            action,
            ActionState.EXTERNAL_ACCEPTED,
            executor_id,
            executor_roles,
            {"tx_id": exec_res.external_transaction_id},
        )

        # Transition through VERIFICATION_PENDING
        cls._transition_state(
            tenant_id,
            action,
            ActionState.VERIFICATION_PENDING,
            executor_id,
            executor_roles,
            {"tx_id": exec_res.external_transaction_id},
        )

        if dry_run or exec_res.transmission_state == "DRY_RUN_SUCCESS":
            cls._transition_state(
                tenant_id,
                action,
                ActionState.VERIFIED,
                executor_id,
                executor_roles,
                {
                    "simulation": True,
                    "verification_mode": "DRY_RUN_EXECUTION_DOUBLE",
                    "no_external_state_change": True,
                    "tx_id": exec_res.external_transaction_id,
                },
            )

            action.execution_state = ActionState.VERIFIED

            return ActionExecutionResult(
                action_id=action_id,
                tenant_id=tenant_id,
                execution_state=ActionState.VERIFIED,
                approval_state=action.approval_state,
                success=True,
                message=(
                    "Dry-run simulation completed successfully and was "
                    "verified by the controlled execution double. No external "
                    "business state was changed."
                ),
                external_transaction_id=exec_res.external_transaction_id,
            )

        # EXTERNAL_ACCEPTED only confirms that the external system
        # accepted/transmitted the request. It does NOT prove that the
        # resulting external business state has been verified.
        #
        # Only an authoritative verification signal may transition
        # the action to VERIFIED.
        verified_confirmed = (
            exec_res.transmission_state == "VERIFIED"
        )

        if verified_confirmed:
            cls._transition_state(
                tenant_id,
                action,
                ActionState.VERIFIED,
                executor_id,
                executor_roles,
                {"tx_id": exec_res.external_transaction_id},
            )
            action.execution_state = ActionState.VERIFIED

            cls._emit_phase13_event(db, tenant_id, action, EventTaxonomy.INVENTORY_UPDATED, "ACTION_VERIFIED")

            return ActionExecutionResult(
                action_id=action_id,
                tenant_id=tenant_id,
                execution_state=ActionState.VERIFIED,
                approval_state=action.approval_state,
                success=True,
                message="Action executed and verified successfully via authoritative confirmation.",
                external_transaction_id=exec_res.external_transaction_id,
            )
        else:
            # EXTERNAL_ACCEPTED means the external system accepted
            # the transmission. It does not prove that the resulting
            # external business state has been verified.
            #
            # Therefore the action is operationally successful but
            # remains VERIFICATION_PENDING until an authoritative
            # verification result is available.
            cls._transition_state(
                tenant_id,
                action,
                ActionState.VERIFICATION_PENDING,
                executor_id,
                executor_roles,
                {
                    "tx_id": exec_res.external_transaction_id,
                    "transmission_state": (
                        exec_res.transmission_state
                    ),
                },
            )

            action.execution_state = (
                ActionState.VERIFICATION_PENDING
            )

            return ActionExecutionResult(
                action_id=action_id,
                tenant_id=tenant_id,
                execution_state=(
                    ActionState.VERIFICATION_PENDING
                ),
                approval_state=action.approval_state,
                success=True,
                message=(
                    "External action was accepted for "
                    "transmission. Authoritative external "
                    "state verification is still pending."
                ),
                external_transaction_id=(
                    exec_res.external_transaction_id
                ),
            )

    @classmethod
    def reconcile_action(
        cls,
        db: Session,
        tenant_id: str,
        action_id: str,
        actor_id: str,
        actor_roles: List[str],
    ) -> ActionExecutionResult:
        """Reconcile an externally submitted action without resubmitting it."""
        action = cls._get_action_or_raise(tenant_id, action_id)
        if action.execution_state != ActionState.EXTERNAL_UNKNOWN:
            return ActionExecutionResult(
                action_id=action_id,
                tenant_id=tenant_id,
                execution_state=action.execution_state,
                approval_state=action.approval_state,
                success=action.execution_state in {ActionState.VERIFIED, ActionState.EXECUTED},
                message="No reconciliation was required because the action is not in EXTERNAL_UNKNOWN state.",
                external_transaction_id=action.external_transaction_id,
            )

        exec_res = ActionExecutionAdapter.reconcile_action(tenant_id, action)
        action.actual_result = exec_res.response_payload
        action.external_transaction_id = exec_res.external_transaction_id or action.external_transaction_id
        action.external_request_id = exec_res.external_request_id or action.idempotency_key

        if exec_res.transmission_state == "VERIFIED" and exec_res.success:
            cls._transition_state(
                tenant_id,
                action,
                ActionState.VERIFIED,
                actor_id,
                actor_roles,
                {"reconciled": True, "tx_id": action.external_transaction_id},
            )
            cls._emit_phase13_event(db, tenant_id, action, EventTaxonomy.INVENTORY_UPDATED, "ACTION_RECONCILED")
            return ActionExecutionResult(
                action_id=action_id,
                tenant_id=tenant_id,
                execution_state=ActionState.VERIFIED,
                approval_state=action.approval_state,
                success=True,
                message="External action reconciled successfully without resubmission.",
                external_transaction_id=action.external_transaction_id,
            )

        cls._transition_state(
            tenant_id,
            action,
            ActionState.MANUAL_INTERVENTION_REQUIRED,
            actor_id,
            actor_roles,
            {"reconciled": False, "error": exec_res.error_message},
        )
        action.error_message = exec_res.error_message
        return ActionExecutionResult(
            action_id=action_id,
            tenant_id=tenant_id,
            execution_state=ActionState.MANUAL_INTERVENTION_REQUIRED,
            approval_state=action.approval_state,
            success=False,
            message="External state could not be reconciled. Manual intervention is required; no resubmission was performed.",
            error_message=exec_res.error_message,
        )

    @classmethod
    def _get_action_or_raise(cls, tenant_id: str, action_id: str) -> ActionContract:
        with cls._lock:
            tenant_actions = cls._ACTIONS_STORE.get(tenant_id, {})
            action = tenant_actions.get(action_id)
        if not action:
            raise KeyError(f"Action with ID '{action_id}' not found for tenant '{tenant_id}'.")
        return action

    @classmethod
    def _transition_state(
        cls,
        tenant_id: str,
        action: ActionContract,
        new_state: ActionState,
        actor_id: str,
        actor_roles: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        with cls._lock:
            prev_state = action.execution_state
            action.execution_state = new_state
        cls._record_audit(
            tenant_id,
            action.action_id,
            actor_id,
            actor_roles[0] if actor_roles else "USER",
            prev_state,
            new_state,
            metadata,
        )
        logger.info("Action [%s] transitioned: %s -> %s (Actor: %s)", action.action_id, prev_state, new_state, actor_id)

    @classmethod
    def _record_audit(
        cls,
        tenant_id: str,
        action_id: str,
        actor_id: str,
        actor_role: str,
        prev_state: Optional[ActionState],
        new_state: ActionState,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        audit_id = f"AUD-{uuid.uuid4().hex[:8].upper()}"
        record = ActionAuditRecord(
            audit_id=audit_id,
            tenant_id=tenant_id,
            action_id=action_id,
            actor_id=actor_id,
            actor_role=actor_role,
            previous_state=prev_state,
            new_state=new_state,
            metadata=metadata or {},
        )
        with cls._lock:
            tenant_audit = cls._AUDIT_STORE.setdefault(tenant_id, [])
            tenant_audit.append(record)

    @classmethod
    def _emit_phase13_event(
        cls,
        db: Session,
        tenant_id: str,
        action: ActionContract,
        taxonomy: EventTaxonomy,
        event_title: str,
    ) -> None:
        """Emits a Phase 13 operational event upon successful action state progression."""
        event = InternalEvent(
            event_id=f"EVT-ACT-{uuid.uuid4().hex[:8].upper()}",
            tenant_id=tenant_id,
            source_system="AURIX_ACTION_ENGINE",
            event_type=taxonomy,
            entity_type=action.entity_type,
            entity_id=action.entity_id,
            changed_fields=["execution_state", "actual_result"],
            event_timestamp=datetime.now(timezone.utc).isoformat(),
            payload_hash=uuid.uuid5(uuid.NAMESPACE_DNS, f"{action.action_id}:{action.execution_state.value}").hex,
            payload={"action_id": action.action_id, "status": action.execution_state.value, "result": action.actual_result},
        )
        EventProcessor.process_event(db, event)
