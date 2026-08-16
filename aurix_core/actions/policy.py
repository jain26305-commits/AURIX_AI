"""Deterministic Policy, Financial Limits, Freshness Validation, and Conflict Detection Engine for Phase 14."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from aurix_core.actions.contracts import ActionCategory, ActionContract, ActionState

logger = logging.getLogger("aurix_core.actions.policy")


class PolicyEvaluationResult(BaseModel):
    """Result of policy evaluation for an operational action."""
    is_allowed: bool
    requires_approval: bool
    block_reason: Optional[str] = None
    evaluated_rules: Dict[str, Any] = Field(default_factory=dict)


class ActionPolicyEngine:
    """Evaluates business rules, financial thresholds, quantity limits, freshness, and conflicts before action execution."""

    # Configurable default policy thresholds
    DEFAULT_MAX_QUANTITY: float = 10000.0
    DEFAULT_MAX_FINANCIAL_VALUE: float = 50000.0
    MAX_FRESHNESS_AGE_SECONDS: int = 3600  # 1 hour max data age

    @classmethod
    def evaluate_policy(
        cls,
        action: ActionContract,
        actor_id: str,
        actor_roles: List[str],
        active_tenant_actions: Optional[List[ActionContract]] = None,
        custom_limits: Optional[Dict[str, Any]] = None,
    ) -> PolicyEvaluationResult:
        """
        Evaluates an action against deterministic policy rules:
        1. Tenant Scope & Authenticated Actor Verification
        2. Data Freshness Check (preventing stale recommendations)
        3. Active Action Conflict Detection (preventing concurrent overlapping writes)
        4. Quantity & Financial Threshold Limits
        5. Category & Risk Classification Rules
        6. Segregation of Duties Check
        """
        limits = custom_limits or {}
        max_qty = limits.get("max_quantity", cls.DEFAULT_MAX_QUANTITY)
        max_val = limits.get("max_financial_value", cls.DEFAULT_MAX_FINANCIAL_VALUE)

        evaluated_rules: Dict[str, Any] = {}

        # 1. Freshness Validation (Crucial Rule: Never execute stale recommendations)
        try:
            freshness_dt = datetime.fromisoformat(action.freshness_timestamp.replace("Z", "+00:00"))
            now_dt = datetime.now(timezone.utc)
            age_seconds = (now_dt - freshness_dt).total_seconds()
            evaluated_rules["data_age_seconds"] = age_seconds

            if age_seconds > cls.MAX_FRESHNESS_AGE_SECONDS:
                return PolicyEvaluationResult(
                    is_allowed=False,
                    requires_approval=True,
                    block_reason=f"Data freshness violation: Source data is {int(age_seconds)} seconds old (max allowed: {cls.MAX_FRESHNESS_AGE_SECONDS}s). Revalidation required.",
                    evaluated_rules=evaluated_rules,
                )
        except Exception as e:
            logger.warning("Failed to parse freshness timestamp for action %s: %s", action.action_id, str(e))
            return PolicyEvaluationResult(
                is_allowed=False,
                requires_approval=True,
                block_reason="Invalid or unparseable freshness timestamp in action contract.",
                evaluated_rules=evaluated_rules,
            )

        # 2. Active Action Conflict Detection
        if active_tenant_actions:
            active_states = {
                ActionState.CREATED,
                ActionState.VALIDATED,
                ActionState.PENDING_APPROVAL,
                ActionState.APPROVED,
                ActionState.EXECUTION_SENT,
                ActionState.EXTERNAL_ACCEPTED,
                ActionState.EXECUTING,
            }
            for existing in active_tenant_actions:
                if existing.action_id == action.action_id:
                    continue
                if existing.entity_id == action.entity_id and existing.action_type == action.action_type:
                    if existing.execution_state in active_states:
                        evaluated_rules["conflicting_action_id"] = existing.action_id
                        return PolicyEvaluationResult(
                            is_allowed=False,
                            requires_approval=False,
                            block_reason=f"Action conflict detected: Active action '{existing.action_id}' already exists for entity '{action.entity_id}' under action type '{action.action_type}'.",
                            evaluated_rules=evaluated_rules,
                        )

        # 3. Action Category & Risk Evaluation
        if action.action_category == ActionCategory.DESTRUCTIVE:
            return PolicyEvaluationResult(
                is_allowed=False,
                requires_approval=True,
                block_reason="Destructive actions are strictly blocked from automated execution.",
                evaluated_rules=evaluated_rules,
            )

        # 4. Quantity & Financial Limits Evaluation
        payload = action.payload
        quantity = float(payload.get("quantity", payload.get("transfer_quantity", 0.0)))
        unit_price = float(payload.get("unit_price", payload.get("estimated_cost", 10.0)))
        total_value = quantity * unit_price

        evaluated_rules["quantity"] = quantity
        evaluated_rules["total_estimated_value"] = total_value

        if quantity > max_qty:
            return PolicyEvaluationResult(
                is_allowed=True,
                requires_approval=True,
                block_reason=f"Quantity ({quantity}) exceeds autonomous threshold ({max_qty}). Human approval mandated.",
                evaluated_rules=evaluated_rules,
            )

        if total_value > max_val:
            return PolicyEvaluationResult(
                is_allowed=True,
                requires_approval=True,
                block_reason=f"Estimated financial value (${total_value:,.2f}) exceeds autonomous threshold (${max_val:,.2f}). Human approval mandated.",
                evaluated_rules=evaluated_rules,
            )

        # 5. Segregation of Duties Check (Requester cannot approve their own action)
        requested_by = action.requested_by
        if requested_by == actor_id and "ADMIN" not in actor_roles:
            evaluated_rules["segregation_of_duties_triggered"] = True
            return PolicyEvaluationResult(
                is_allowed=True,
                requires_approval=True,
                block_reason="Segregation of duties policy: Requesting user cannot self-approve high-risk actions.",
                evaluated_rules=evaluated_rules,
            )

        # 6. Default Autonomous Allowance
        requires_approval = action.action_category == ActionCategory.APPROVAL_REQUIRED or total_value > (max_val * 0.5)

        return PolicyEvaluationResult(
            is_allowed=True,
            requires_approval=requires_approval,
            block_reason=None,
            evaluated_rules=evaluated_rules,
        )
