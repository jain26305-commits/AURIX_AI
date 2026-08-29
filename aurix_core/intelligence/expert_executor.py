"""
AURIX Expert Executor.

Controlled execution boundary between:
    Evidence preparation
        ↓
    Expert contracts
        ↓
    Expert registry
        ↓
    Existing deterministic expert engine

The executor does not implement domain mathematics.
Existing expert engines remain authoritative.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from aurix_core.intelligence.expert_contracts import (
    ExpertContractRegistry,
)
from aurix_core.intelligence.expert_registry import (
    ExpertBinding,
    ExpertRegistry,
)


@dataclass
class ExpertExecutionResult:
    """Structured result of controlled expert execution."""

    decision: str
    status: str = "BLOCKED"

    executed: bool = False
    result: Any = None

    execution_path: str = "SPECIALIST_ENGINE"

    required_sources: List[str] = field(default_factory=list)
    available_sources: List[str] = field(default_factory=list)
    missing_sources: List[str] = field(default_factory=list)

    missing_fields: List[str] = field(default_factory=list)

    blockers: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)

    provenance: Dict[str, Any] = field(default_factory=dict)

    error: Optional[str] = None


class ExpertExecutor:
    """
    Single controlled execution gateway for registered expert engines.
    """

    @classmethod
    def execute(
        cls,
        *,
        decision: str,
        prepared_inputs: Optional[Dict[str, Any]] = None,
        available_sources: Optional[List[str]] = None,
        missing_sources: Optional[List[str]] = None,
        missing_fields: Optional[List[str]] = None,
        tenant_id: Optional[str] = None,
        provenance: Optional[Dict[str, Any]] = None,
    ) -> ExpertExecutionResult:

        decision_key = str(decision).strip().upper()

        prepared = dict(prepared_inputs or {})
        available = list(available_sources or [])
        unavailable = list(missing_sources or [])
        supplied_missing_fields = list(missing_fields or [])

        execution_provenance: Dict[str, Any] = {
            **dict(provenance or {}),
            "answer_source": "AURIX_ENGINE",
            "executor": "ExpertExecutor",
            "decision": decision_key,
            "tenant_id": tenant_id,
        }

        # ======================================================
        # 1. Resolve expert contract
        # ======================================================

        try:
            contract = ExpertContractRegistry.get(decision_key)
        except KeyError as exc:
            return cls._blocked(
                decision=decision_key,
                blockers=["UNKNOWN_EXPERT_CONTRACT"],
                limitations=[str(exc)],
                provenance=execution_provenance,
            )

        if not contract.execution_allowed:
            return cls._blocked(
                decision=decision_key,
                blockers=["EXECUTION_NOT_ALLOWED_BY_CONTRACT"],
                limitations=[
                    "The expert contract explicitly prohibits direct execution."
                ],
                provenance={
                    **execution_provenance,
                    "contract_execution_allowed": False,
                    "expert_executed": False,
                },
            )

        required_sources = list(contract.required_sources)

        # ======================================================
        # 2. Required evidence gate
        # ======================================================

        available_set = set(available)
        unavailable_set = set(unavailable)

        unresolved_sources = [
            source
            for source in required_sources
            if source not in available_set
            or source in unavailable_set
        ]

        if unresolved_sources:
            return ExpertExecutionResult(
                decision=decision_key,
                status="BLOCKED",
                executed=False,
                execution_path="SPECIALIST_ENGINE",
                required_sources=required_sources,
                available_sources=available,
                missing_sources=unresolved_sources,
                missing_fields=[],
                blockers=list(unresolved_sources),
                limitations=[
                    "Required evidence is unavailable."
                ],
                provenance={
                    **execution_provenance,
                    "contract_execution_allowed": False,
                },
            )

        # ======================================================
        # 3. Required field gate
        # ======================================================

        required_fields = [
            field.name
            for field in contract.fields
            if field.required
        ]

        missing_required_fields: List[str] = []

        for field_name in required_fields:

            if field_name in supplied_missing_fields:
                missing_required_fields.append(field_name)
                continue

            if field_name not in prepared:
                missing_required_fields.append(field_name)
                continue

            value = prepared[field_name]

            if value is None:
                missing_required_fields.append(field_name)
                continue

            if isinstance(
                value,
                (list, tuple, set, dict),
            ) and not value:
                missing_required_fields.append(field_name)

        if missing_required_fields:
            return ExpertExecutionResult(
                decision=decision_key,
                status="BLOCKED",
                executed=False,
                execution_path="SPECIALIST_ENGINE",
                required_sources=required_sources,
                available_sources=available,
                missing_sources=[],
                missing_fields=missing_required_fields,
                blockers=list(missing_required_fields),
                limitations=[
                    "Required expert inputs are unavailable."
                ],
                provenance={
                    **execution_provenance,
                    "contract_execution_allowed": False,
                },
            )

        # ======================================================
        # 4. Resolve exact registry binding
        # ======================================================

        try:
            binding = ExpertRegistry.get(decision_key)
        except KeyError as exc:
            return ExpertExecutionResult(
                decision=decision_key,
                status="BLOCKED",
                executed=False,
                execution_path="SPECIALIST_ENGINE",
                required_sources=required_sources,
                available_sources=available,
                blockers=["EXPERT_BINDING_UNAVAILABLE"],
                limitations=[str(exc)],
                provenance={
                    **execution_provenance,
                    "contract_execution_allowed": False,
                },
            )

        # ======================================================
        # 5. Load exact registered method
        # ======================================================

        try:
            method = ExpertRegistry.load_method(binding)
        except Exception as exc:
            return ExpertExecutionResult(
                decision=decision_key,
                status="BLOCKED",
                executed=False,
                execution_path="SPECIALIST_ENGINE",
                required_sources=required_sources,
                available_sources=available,
                blockers=["EXPERT_METHOD_UNAVAILABLE"],
                limitations=[
                    "Registered expert method could not be loaded."
                ],
                provenance={
                    **execution_provenance,
                    "contract_execution_allowed": False,
                    "expert_binding": cls._binding_metadata(binding),
                },
                error=f"{type(exc).__name__}: {exc}",
            )

        # ======================================================
        # 6. Contract-controlled input projection
        # ======================================================

        allowed_fields = {
            field.name
            for field in contract.fields
        }

        execution_inputs = {
            key: value
            for key, value in prepared.items()
            if key in allowed_fields
        }

        # Tenant identity is execution context, not business evidence.
        # Pass it only when the registered engine accepts it.
        if tenant_id is not None:
            execution_inputs["tenant_id"] = tenant_id

        # ======================================================
        # 7. Validate against actual expert method signature
        # ======================================================

        try:
            signature = inspect.signature(method)

            accepts_kwargs = any(
                parameter.kind
                == inspect.Parameter.VAR_KEYWORD
                for parameter in signature.parameters.values()
            )

            if not accepts_kwargs:
                execution_inputs = {
                    key: value
                    for key, value in execution_inputs.items()
                    if key in signature.parameters
                }

            bound = signature.bind_partial(
                **execution_inputs
            )

            unresolved_parameters: List[str] = []

            for name, parameter in signature.parameters.items():

                if name in {"self", "cls"}:
                    continue

                if parameter.default is not inspect.Parameter.empty:
                    continue

                if name not in bound.arguments:
                    unresolved_parameters.append(name)

            if unresolved_parameters:
                return ExpertExecutionResult(
                    decision=decision_key,
                    status="BLOCKED",
                    executed=False,
                    execution_path="SPECIALIST_ENGINE",
                    required_sources=required_sources,
                    available_sources=available,
                    missing_fields=unresolved_parameters,
                    blockers=unresolved_parameters,
                    limitations=[
                        "Expert method arguments could not be fully resolved."
                    ],
                    provenance={
                        **execution_provenance,
                        "contract_execution_allowed": False,
                        "expert_binding": cls._binding_metadata(binding),
                    },
                )

        except (TypeError, ValueError):
            # Some callables may not expose a normal inspect signature.
            # The registry itself remains authoritative.
            pass

        # ======================================================
        # 8. Execute registered expert
        # ======================================================

        try:
            expert_result = method(
                **execution_inputs
            )

        except Exception as exc:
            return ExpertExecutionResult(
                decision=decision_key,
                status="EXECUTION_FAILED",
                executed=False,
                result=None,
                execution_path="SPECIALIST_ENGINE",
                required_sources=required_sources,
                available_sources=available,
                blockers=["EXPERT_EXECUTION_ERROR"],
                limitations=[
                    "Registered expert engine execution failed."
                ],
                provenance={
                    **execution_provenance,
                    "contract_execution_allowed": True,
                    "expert_executed": False,
                    "expert_binding": cls._binding_metadata(binding),
                },
                error=f"{type(exc).__name__}: {exc}",
            )

        # ======================================================
        # 9. Successful execution
        # ======================================================

        return ExpertExecutionResult(
            decision=decision_key,
            status="EXECUTED",
            executed=True,
            result=expert_result,
            execution_path="SPECIALIST_ENGINE",
            required_sources=required_sources,
            available_sources=available,
            missing_sources=[],
            missing_fields=[],
            blockers=[],
            limitations=[],
            provenance={
                **execution_provenance,
                "contract_execution_allowed": True,
                "expert_executed": True,
                "expert_binding": cls._binding_metadata(binding),
            },
        )

    @staticmethod
    def _binding_metadata(
        binding: ExpertBinding,
    ) -> Dict[str, Any]:
        """
        Return only canonical registry metadata.
        """

        return {
            "decision": binding.decision,
            "domain": binding.domain,
            "module_path": binding.module_path,
            "class_name": binding.class_name,
            "method_name": binding.method_name,
            "import_path": binding.import_path,
        }

    @staticmethod
    def _blocked(
        *,
        decision: str,
        blockers: List[str],
        limitations: List[str],
        provenance: Dict[str, Any],
    ) -> ExpertExecutionResult:

        return ExpertExecutionResult(
            decision=decision,
            status="BLOCKED",
            executed=False,
            execution_path="SPECIALIST_ENGINE",
            blockers=blockers,
            limitations=limitations,
            provenance={
                **provenance,
                "contract_execution_allowed": False,
                "expert_executed": False,
            },
        )


__all__ = [
    "ExpertExecutionResult",
    "ExpertExecutor",
]
