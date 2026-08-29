"""
AURIX Enterprise Agent Studio — Agent Builder Control Plane
Phase 30 Core Implementation.
Manages agent drafting, property updates, version snapshots, and skill/tool binding.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from aurix_core.studio.contracts import (
    StudioAgentDraft,
    StudioAgentStatus,
    StudioAgentVersion,
)


class AgentBuilder:
    """Administrative control plane for constructing and versioning enterprise agents."""

    _drafts: Dict[str, StudioAgentDraft] = {}
    _versions: Dict[str, List[StudioAgentVersion]] = {}

    @classmethod
    def create_agent_draft(
        cls,
        draft: StudioAgentDraft,
        db: Optional[Session] = None,
    ) -> StudioAgentDraft:
        """Create or initialize a new agent draft."""
        cls._drafts[draft.agent_id] = draft
        if db is not None:
            try:
                from aurix_core.database.models.studio import StudioAgentModel
                rec = db.query(StudioAgentModel).filter(StudioAgentModel.id == draft.agent_id).first()
                if not rec:
                    rec = StudioAgentModel(
                        id=draft.agent_id,
                        tenant_id=draft.tenant_id,
                        name=draft.name,
                        business_purpose=draft.business_purpose,
                        domain=draft.domain,
                        owner=draft.owner,
                        agent_type=draft.agent_type,
                        version=draft.version,
                        status=draft.status.value,
                        allowed_skills_json=draft.allowed_skills,
                        allowed_tools_json=draft.allowed_tools,
                        context_domains_json=draft.allowed_context_domains,
                        risk_classification=draft.risk_classification,
                        max_steps=draft.max_steps_per_execution,
                        budget_limit_usd=draft.budget_limit_usd,
                    )
                    db.add(rec)
                    db.commit()
            except Exception:
                db.rollback()
        return draft

    @classmethod
    def get_agent_draft(cls, agent_id: str, db: Optional[Session] = None) -> Optional[StudioAgentDraft]:
        """Retrieve agent draft from DB or memory cache."""
        if agent_id in cls._drafts:
            return cls._drafts[agent_id]
        if db is not None:
            from aurix_core.database.models.studio import StudioAgentModel
            rec = db.query(StudioAgentModel).filter(StudioAgentModel.id == agent_id).first()
            if rec:
                draft = StudioAgentDraft(
                    agent_id=rec.id,
                    tenant_id=rec.tenant_id,
                    name=rec.name,
                    business_purpose=rec.business_purpose,
                    domain=rec.domain,
                    owner=rec.owner,
                    agent_type=rec.agent_type,
                    version=rec.version,
                    status=StudioAgentStatus(rec.status),
                    allowed_skills=rec.allowed_skills_json or [],
                    allowed_tools=rec.allowed_tools_json or [],
                    allowed_context_domains=rec.context_domains_json or [],
                    risk_classification=rec.risk_classification,
                    max_steps_per_execution=rec.max_steps,
                    budget_limit_usd=rec.budget_limit_usd,
                )
                cls._drafts[rec.id] = draft
                return draft
        return None

    @classmethod
    def list_agents(cls, tenant_id: str = "GLOBAL", db: Optional[Session] = None) -> List[StudioAgentDraft]:
        """List all studio agent definitions for a tenant."""
        if db is not None:
            from aurix_core.database.models.studio import StudioAgentModel
            recs = db.query(StudioAgentModel).filter(
                (StudioAgentModel.tenant_id == tenant_id) | (StudioAgentModel.tenant_id == "GLOBAL")
            ).all()
            for r in recs:
                if r.id not in cls._drafts:
                    cls._drafts[r.id] = StudioAgentDraft(
                        agent_id=r.id,
                        tenant_id=r.tenant_id,
                        name=r.name,
                        business_purpose=r.business_purpose,
                        domain=r.domain,
                        owner=r.owner,
                        agent_type=r.agent_type,
                        version=r.version,
                        status=StudioAgentStatus(r.status),
                        allowed_skills=r.allowed_skills_json or [],
                        allowed_tools=r.allowed_tools_json or [],
                        allowed_context_domains=r.context_domains_json or [],
                        risk_classification=r.risk_classification,
                        max_steps_per_execution=r.max_steps,
                        budget_limit_usd=r.budget_limit_usd,
                    )
        return [a for a in cls._drafts.values() if a.tenant_id in (tenant_id, "GLOBAL")]

    @classmethod
    def publish_agent_version(
        cls,
        agent_id: str,
        published_by: str,
        change_summary: str = "",
        db: Optional[Session] = None,
    ) -> StudioAgentVersion:
        """Publish an immutable version snapshot of an agent draft."""
        draft = cls.get_agent_draft(agent_id, db=db)
        if not draft:
            raise ValueError(f"Agent draft {agent_id} not found.")

        draft.status = StudioAgentStatus.PUBLISHED
        version_snapshot = StudioAgentVersion(
            agent_id=draft.agent_id,
            tenant_id=draft.tenant_id,
            version_number=draft.version,
            status=StudioAgentStatus.PUBLISHED,
            config_snapshot_json=draft.model_dump(),
            published_by=published_by,
            change_summary=change_summary,
        )

        cls._versions.setdefault(agent_id, []).append(version_snapshot)

        if db is not None:
            try:
                from aurix_core.database.models.studio import StudioAgentModel, StudioAgentVersionModel
                agt_rec = db.query(StudioAgentModel).filter(StudioAgentModel.id == agent_id).first()
                if agt_rec:
                    agt_rec.status = StudioAgentStatus.PUBLISHED.value
                ver_rec = StudioAgentVersionModel(
                    id=version_snapshot.version_id,
                    agent_id=version_snapshot.agent_id,
                    tenant_id=version_snapshot.tenant_id,
                    version_number=version_snapshot.version_number,
                    status=version_snapshot.status.value,
                    config_snapshot_json=version_snapshot.config_snapshot_json,
                    published_by=version_snapshot.published_by,
                    change_summary=version_snapshot.change_summary,
                )
                db.add(ver_rec)
                db.commit()
            except Exception:
                db.rollback()

        return version_snapshot
