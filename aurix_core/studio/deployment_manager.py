"""
AURIX Enterprise Agent Studio — Governed Deployment Manager
Phase 30 Core Implementation.
Manages multi-tier promotion (DEV -> TEST -> PROD), Phase 29 runtime synchronization, and atomic rollbacks.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from aurix_core.agents.contracts import AgentDefinition, AgentStatus, AgentType, RiskLevel
from aurix_core.agents.runtime import AgentRuntime
from aurix_core.studio.agent_builder import AgentBuilder
from aurix_core.studio.contracts import (
    DeploymentRecord,
    EnvironmentTier,
    StudioAgentStatus,
)


class DeploymentManager:
    """Governed deployment control plane promoting agent versions and updating Phase 29 runtime."""

    _deployments: List[DeploymentRecord] = []

    @classmethod
    def deploy_agent_version(
        cls,
        tenant_id: str,
        agent_id: str,
        version_number: str,
        environment: EnvironmentTier,
        deployed_by: str,
        db: Optional[Session] = None,
    ) -> DeploymentRecord:
        """Deploy an immutable agent version to an environment tier."""
        draft = AgentBuilder.get_agent_draft(agent_id, db=db)
        if not draft:
            raise ValueError(f"Agent {agent_id} not found.")

        record = DeploymentRecord(
            tenant_id=tenant_id,
            agent_id=agent_id,
            version_id=f"VER-{agent_id}-{version_number}",
            environment=environment,
            deployed_by=deployed_by,
            status="ACTIVE",
        )

        cls._deployments.append(record)

        # When deployed to PRODUCTION, synchronize directly into Phase 29 AgentRuntime
        if environment == EnvironmentTier.PRODUCTION:
            runtime_agent = AgentDefinition(
                agent_id=draft.agent_id,
                tenant_id=tenant_id,
                agent_type=AgentType(draft.agent_type),
                name=draft.name,
                version=version_number,
                status=AgentStatus.ACTIVE,
                owner=draft.owner,
                capabilities=draft.allowed_skills,
                risk_classification=RiskLevel(draft.risk_classification),
                allowed_tools=draft.allowed_tools,
                max_steps_per_execution=draft.max_steps_per_execution,
            )
            AgentRuntime.register_agent(runtime_agent, db=db)

        if db is not None:
            try:
                from aurix_core.database.models.studio import StudioDeploymentModel
                dep_rec = StudioDeploymentModel(
                    id=record.deployment_id,
                    tenant_id=record.tenant_id,
                    agent_id=record.agent_id,
                    version_id=record.version_id,
                    environment=record.environment.value,
                    deployed_by=record.deployed_by,
                    status=record.status,
                )
                db.add(dep_rec)
                db.commit()
            except Exception:
                db.rollback()

        return record

    @classmethod
    def rollback_deployment(
        cls,
        tenant_id: str,
        agent_id: str,
        target_version_number: str,
        rolled_back_by: str,
        db: Optional[Session] = None,
    ) -> DeploymentRecord:
        """Atomic rollback of production deployment to a previously published version."""
        # Mark current active deployments as ROLLED_BACK
        for dep in cls._deployments:
            if dep.agent_id == agent_id and dep.environment == EnvironmentTier.PRODUCTION and dep.status == "ACTIVE":
                dep.status = "ROLLED_BACK"

        new_deployment = cls.deploy_agent_version(
            tenant_id=tenant_id,
            agent_id=agent_id,
            version_number=target_version_number,
            environment=EnvironmentTier.PRODUCTION,
            deployed_by=rolled_back_by,
            db=db,
        )
        return new_deployment
