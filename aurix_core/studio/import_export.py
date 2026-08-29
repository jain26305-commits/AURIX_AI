"""
AURIX Enterprise Agent Studio — Governed Import / Export Engine
Phase 30 Core Implementation.
Safely serializes and validates agent/workflow configuration bundles with secret redaction.
"""

from __future__ import annotations

from typing import Any, Dict
from aurix_core.studio.contracts import StudioAgentDraft
from aurix_core.studio.secret_manager import StudioSecretManager


class StudioImportExport:
    """Governed import and export serializer for enterprise agent packages."""

    @classmethod
    def export_agent_bundle(cls, draft: StudioAgentDraft) -> Dict[str, Any]:
        """Serialize agent draft into a sanitized export bundle."""
        raw = draft.model_dump()
        return {
            "bundle_type": "AURIX_STUDIO_AGENT_PACKAGE",
            "version": "1.0",
            "agent_payload": StudioSecretManager.sanitize_config_for_export(raw),
        }

    @classmethod
    def import_agent_bundle(cls, tenant_id: str, bundle: Dict[str, Any]) -> StudioAgentDraft:
        """Validate and construct an agent draft from an imported package."""
        if bundle.get("bundle_type") != "AURIX_STUDIO_AGENT_PACKAGE":
            raise ValueError("Invalid bundle format. Expected AURIX_STUDIO_AGENT_PACKAGE.")

        payload = bundle.get("agent_payload", {})
        payload["tenant_id"] = tenant_id  # Enforce importing tenant isolation
        return StudioAgentDraft(**payload)
