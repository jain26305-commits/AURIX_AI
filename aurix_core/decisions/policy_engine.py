"""
AURIX Deterministic Decision Engine 2.0 — Policy-as-Code Engine
Phase 27 Core Implementation.
Declarative governance rule engine enforcing financial thresholds, dual-authorization requirements, and escalation triggers.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from aurix_core.decisions.contracts import (
    DecisionCandidate,
    DecisionDomain,
    DecisionPolicy,
)


class PolicyEngine:
    """Evaluates Policy-as-Code rules to determine authorization and approval gates."""

    _policy_store: Dict[str, List[DecisionPolicy]] = {}

    @classmethod
    def get_policies(cls, tenant_id: str) -> List[DecisionPolicy]:
        """Retrieve tenant policies with standard defaults."""
        return cls._policy_store.get(
            tenant_id,
            [
                DecisionPolicy(
                    tenant_id=tenant_id,
                    policy_name="HIGH_EXPENDITURE_DUAL_APPROVAL",
                    decision_domain=DecisionDomain.PROCUREMENT_SUPPLIER,
                    min_financial_threshold_usd=25000.0,
                    requires_dual_approval=True,
                    required_approver_role="CFO",
                    auto_executable=False,
                ),
                DecisionPolicy(
                    tenant_id=tenant_id,
                    policy_name="STANDARD_SUPPLIER_REALLOCATION_RULE",
                    decision_domain=DecisionDomain.PROCUREMENT_SUPPLIER,
                    min_financial_threshold_usd=5000.0,
                    requires_dual_approval=False,
                    required_approver_role="PROCUREMENT_MANAGER",
                    auto_executable=False,
                ),
            ],
        )

    @classmethod
    def evaluate_policy_requirements(
        cls,
        tenant_id: str,
        domain: DecisionDomain,
        recommended_candidate: DecisionCandidate,
    ) -> Dict[str, Any]:
        """Evaluate applicable policies against recommended candidate action."""
        policies = [p for p in cls.get_policies(tenant_id) if p.decision_domain == domain and p.is_active]

        requires_approval = False
        dual_approval = False
        approver_role: Optional[str] = None
        matched_policy_id: Optional[str] = None

        for pol in policies:
            if recommended_candidate.cost_usd >= pol.min_financial_threshold_usd:
                requires_approval = True
                dual_approval = pol.requires_dual_approval
                approver_role = pol.required_approver_role
                matched_policy_id = pol.policy_id
                break

        return {
            "approval_required": requires_approval,
            "requires_dual_approval": dual_approval,
            "required_approver_role": approver_role,
            "policy_id": matched_policy_id,
            "is_auto_executable": not requires_approval,
        }
