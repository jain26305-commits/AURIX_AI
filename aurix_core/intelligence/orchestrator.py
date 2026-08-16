"""Master Orchestrator for Phase 9 Executive & AI Intelligence."""

import datetime
import uuid
from typing import Any, Dict, List, Optional
from aurix_core.intelligence.causal import EvidenceChainBuilder
from aurix_core.intelligence.config import IntelligenceConfiguration
from aurix_core.intelligence.narrative import ExecutiveNarrativeGenerator
from aurix_core.intelligence.priorities import ActionPrioritizer
from aurix_core.intelligence.signals import SignalExtractor
from aurix_core.schema.phase5_contract import MissingInput
from aurix_core.schema.phase8_contract import Phase8InputContract
from aurix_core.schema.phase9_contract import Phase9InputContract
from aurix_core.schema.phase10_contract import Phase10InputContract
from aurix_core.schema.phase11_contract import AIInterpretation, Phase11InputContract

__all__ = ["Phase9Orchestrator"]


class Phase9Orchestrator:
    """Master Orchestrator for Phase 9 Executive & AI Intelligence."""

    def __init__(
        self,
        phase7a_network_output: Optional[Dict[str, Any]] = None,
        phase7b_decision_output: Optional[Dict[str, Any]] = None,
        phase8_economics_output: Optional[Dict[str, Any]] = None,
        config_override: Optional[Any] = None,
    ) -> None:
        self.phase7a_data = phase7a_network_output or {}
        self.phase7b_data = phase7b_decision_output or {}
        self.phase8_data = phase8_economics_output or {}

        if isinstance(config_override, IntelligenceConfiguration):
            self.config = config_override
        elif isinstance(config_override, dict):
            self.config = IntelligenceConfiguration(config_override)
        else:
            self.config = IntelligenceConfiguration()

        self.run_id = str(uuid.uuid4())
        self.timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

    def execute(self) -> Dict[str, Any]:
        """Executes the complete Phase 9 intelligence pipeline and returns dictionary output."""
        contract = self.process_intelligence()
        return contract.model_dump()

    def process_intelligence(self) -> Phase11InputContract:
        """Consumes Phase 7A, 7B, and 8 contracts to generate signals, priorities, chains, and executive narratives."""
        missing_inputs: List[MissingInput] = []
        limitations: List[str] = []

        # Parse Upstream Contracts
        p7a_contract: Optional[Phase8InputContract] = None
        if self.phase7a_data:
            p7a_contract = Phase8InputContract(**self.phase7a_data)

        p7b_contract: Optional[Phase9InputContract] = None
        if self.phase7b_data:
            p7b_contract = Phase9InputContract(**self.phase7b_data)

        p8_contract: Optional[Phase10InputContract] = None
        if self.phase8_data:
            p8_contract = Phase10InputContract(**self.phase8_data)

        if not p7a_contract and not p7b_contract and not p8_contract:
            missing_inputs.append(
                MissingInput(
                    field="upstream_analytical_outputs",
                    state="USER_INPUT_REQUIRED",
                    domain="intelligence",
                    severity="CRITICAL",
                    prompt="No upstream analytical outputs provided for Phase 9 Executive Intelligence.",
                )
            )
            return Phase11InputContract(
                status="USER_INPUT_REQUIRED",
                missing_inputs=missing_inputs,
                signals=[],
                prioritized_actions=[],
                evidence_chains=[],
                executive_summary=None,
                ai_interpretation=None,
                limitations=["MISSING_ALL_UPSTREAM_ANALYTICAL_INPUTS"],
                provenance={
                    "phase9_run_id": self.run_id,
                    "timestamp": self.timestamp,
                    "engine_version": "9.0.0-executive-intelligence",
                },
            )

        # 1. Signal Extraction Engine
        signals = SignalExtractor.extract_signals(
            phase7a_contract=p7a_contract,
            phase7b_contract=p7b_contract,
            phase8_contract=p8_contract,
            config=self.config,
        )

        # 2. Multi-Dimensional Action Prioritization
        actions = ActionPrioritizer.prioritize_signals(
            signals=signals,
            config=self.config,
        )

        # 3. Evidence Chain Builder
        chains = EvidenceChainBuilder.build_evidence_chains(
            signals=signals,
            phase7a_contract=p7a_contract,
            phase7b_contract=p7b_contract,
            phase8_contract=p8_contract,
            config=self.config,
        )

        # 4. Executive Summary Narrative Generator
        summary = ExecutiveNarrativeGenerator.generate_summary(
            signals=signals,
            actions=actions,
            chains=chains,
            config=self.config,
        )

        # 5. Optional AI Grounded Interpretation Container
        ai_interp: Optional[AIInterpretation] = None
        if self.config.enable_ai_interpretation:
            ai_interp = AIInterpretation(
                is_generated=False,
                model_info="DETERMINISTIC_GROUNDED_FALLBACK",
                grounded_narrative=summary.headline,
                source_attribution_ids=[s.signal_id for s in signals],
                validation_status="GROUNDED_FACTS_ONLY",
                fallback_used=True,
            )

        p8_run_id = p8_contract.provenance.get("phase8_run_id", "UNKNOWN") if p8_contract else "UNKNOWN"
        p7b_run_id = p7b_contract.provenance.get("phase7b_run_id", "UNKNOWN") if p7b_contract else "UNKNOWN"

        overall_status = "COMPUTABLE" if signals else "NO_SIGNALS_DETECTED"

        return Phase11InputContract(
            status=overall_status,
            missing_inputs=missing_inputs,
            signals=signals,
            prioritized_actions=actions,
            evidence_chains=chains,
            executive_summary=summary,
            ai_interpretation=ai_interp,
            limitations=limitations,
            provenance={
                "phase9_run_id": self.run_id,
                "phase8_run_id": p8_run_id,
                "phase7b_run_id": p7b_run_id,
                "timestamp": self.timestamp,
                "engine_version": "9.0.0-executive-intelligence",
            },
        )