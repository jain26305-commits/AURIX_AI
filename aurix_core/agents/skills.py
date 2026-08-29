"""
AURIX Governed Autonomous Agents — Skill Registry
Phase 29 Production Hardened.
Manages bounded enterprise capabilities with semver compatibility checking and dynamic discovery.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from aurix_core.agents.contracts import ReversibilityStatus, RiskLevel, SkillDefinition


class SkillRegistry:
    """Governed repository of enterprise skills with dynamic discovery and versioning."""

    _skills: Dict[str, SkillDefinition] = {
        "propose_po_split": SkillDefinition(
            skill_id="SKL-PO-SPLIT",
            name="propose_po_split",
            version="1.2.0",
            description="Reallocate purchase order volume to secondary backup vendor.",
            risk_level=RiskLevel.HIGH,
            requires_approval=True,
            side_effect=ReversibilityStatus.REVERSIBLE,
        ),
        "analyze_invoice": SkillDefinition(
            skill_id="SKL-INV-ANALYSIS",
            name="analyze_invoice",
            version="1.0.0",
            description="Inspect billing records for 3-way match exceptions and pricing variance.",
            risk_level=RiskLevel.LOW,
            requires_approval=False,
            side_effect=ReversibilityStatus.REVERSIBLE,
        ),
    }

    @classmethod
    def is_version_compatible(cls, required_version: str, available_version: str) -> bool:
        """Evaluate semantic version compatibility (e.g., ^1.0 or >=1.0)."""
        req = required_version.lstrip("^>=").strip()
        avail = available_version.strip()
        req_major = req.split(".")[0] if "." in req else req
        avail_major = avail.split(".")[0] if "." in avail else avail
        return req_major == avail_major

    @classmethod
    def register_skill(cls, skill: SkillDefinition, db: Optional[Session] = None) -> SkillDefinition:
        """Register or update a skill in durable persistence and memory cache."""
        cls._skills[skill.name] = skill
        if db is not None:
            from aurix_core.database.models.agents import SkillRegistryModel
            rec = db.query(SkillRegistryModel).filter(SkillRegistryModel.name == skill.name).first()
            if not rec:
                rec = SkillRegistryModel(
                    id=skill.skill_id,
                    name=skill.name,
                    version=skill.version,
                    description=skill.description,
                    risk_level=skill.risk_level.value,
                    requires_approval=skill.requires_approval,
                    side_effect=skill.side_effect.value,
                )
                db.add(rec)
            else:
                rec.version = skill.version
                rec.description = skill.description
                rec.risk_level = skill.risk_level.value
            try:
                db.commit()
            except Exception:
                db.rollback()
        return skill

    @classmethod
    def get_skill(cls, skill_name: str, db: Optional[Session] = None) -> Optional[SkillDefinition]:
        """Retrieve skill definition from DB or cache."""
        if skill_name in cls._skills:
            return cls._skills[skill_name]
        if db is not None:
            from aurix_core.database.models.agents import SkillRegistryModel
            rec = db.query(SkillRegistryModel).filter(SkillRegistryModel.name == skill_name).first()
            if rec:
                skill = SkillDefinition(
                    skill_id=rec.id,
                    name=rec.name,
                    version=rec.version,
                    description=rec.description,
                    risk_level=RiskLevel(rec.risk_level),
                    requires_approval=rec.requires_approval,
                    side_effect=ReversibilityStatus(rec.side_effect),
                )
                cls._skills[rec.name] = skill
                return skill
        return None

    @classmethod
    def list_skills(cls, db: Optional[Session] = None) -> List[SkillDefinition]:
        """List all discoverable skills."""
        if db is not None:
            from aurix_core.database.models.agents import SkillRegistryModel
            recs = db.query(SkillRegistryModel).all()
            for rec in recs:
                if rec.name not in cls._skills:
                    cls._skills[rec.name] = SkillDefinition(
                        skill_id=rec.id,
                        name=rec.name,
                        version=rec.version,
                        description=rec.description,
                        risk_level=RiskLevel(rec.risk_level),
                        requires_approval=rec.requires_approval,
                        side_effect=ReversibilityStatus(rec.side_effect),
                    )
        return list(cls._skills.values())
