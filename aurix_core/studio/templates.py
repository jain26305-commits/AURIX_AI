"""
AURIX Enterprise Agent Studio — Template Catalog
Phase 30 Core Implementation.
Repository of pre-governed enterprise agent and visual workflow templates.
"""

from __future__ import annotations

from typing import Dict, List
from aurix_core.studio.contracts import StudioTemplate


class TemplateCatalog:
    """Pre-configured enterprise agent and workflow template repository."""

    _templates: Dict[str, StudioTemplate] = {
        "TPL-COLL-01": StudioTemplate(
            template_id="TPL-COLL-01",
            template_type="AGENT",
            name="AR Collections & Aging Review Agent",
            category="FINANCE",
            description="Inspects 60+ day overdue customer invoices and prepares governed reminder actions.",
            suggested_risk="MEDIUM",
            definition_json={
                "agent_type": "FINANCE_AGENT",
                "allowed_skills": ["analyze_invoice"],
                "allowed_tools": ["ERP_INVOICE_API"],
                "max_steps": 8,
            },
        ),
        "TPL-SUPP-01": StudioTemplate(
            template_id="TPL-SUPP-01",
            template_type="AGENT",
            name="Supplier Delay & Order Split Agent",
            category="PROCUREMENT",
            description="Detects supply port delays and proposes order splitting with secondary certified vendors.",
            suggested_risk="HIGH",
            definition_json={
                "agent_type": "PROCUREMENT_AGENT",
                "allowed_skills": ["propose_po_split"],
                "allowed_tools": ["ERP_PO_API"],
                "max_steps": 10,
            },
        ),
    }

    @classmethod
    def list_templates(cls) -> List[StudioTemplate]:
        """List all available pre-governed templates."""
        return list(cls._templates.values())

    @classmethod
    def get_template(cls, template_id: str) -> StudioTemplate | None:
        """Retrieve a specific template by ID."""
        return cls._templates.get(template_id)
