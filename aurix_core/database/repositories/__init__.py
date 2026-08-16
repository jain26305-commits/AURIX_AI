"""Canonical AURIX database repository exports.

This package exposes one authoritative repository implementation per domain.
Network repositories are imported from the canonical ``network`` module;
legacy ``network_intelligence`` repository declarations are intentionally not
loaded here.
"""

from aurix_core.database.repositories.base import BaseRepository
from aurix_core.database.repositories.supply_intelligence import (
    SupplyIntelligenceRunRepository,
    SupplierPerformanceRepository,
    ReplenishmentRecommendationRepository,
)
from aurix_core.database.repositories.logistics_intelligence import (
    LogisticsIntelligenceRunRepository,
    CarrierPerformanceRepository,
    LanePerformanceRepository,
    ShipmentEvaluationRepository,
)
from aurix_core.database.repositories.network import (
    NetworkFlowRunRepository,
    NetworkNodeSnapshotRepository,
    NetworkEdgeSnapshotRepository,
    NetworkRiskSnapshotRepository,
    NetworkOptimizationRunRepository,
    NetworkIntelligenceRunRepository,
    NetworkRiskEventRepository,
)
from aurix_core.database.repositories.economics import (
    FinancialIntelligenceRunRepository,
    FinancialBaselineSnapshotRepository,
    ScenarioRunRepository,
    ScenarioMetricSnapshotRepository,
)
from aurix_core.database.repositories.intelligence import (
    IntelligenceRunRepository,
    CapabilityStateRepository,
    IntelligenceSnapshotRepository,
    BusinessSignalRepository,
    PrioritizedActionRepository,
    ExecutiveSummaryRepository,
    ConversationRepository,
    ConversationMessageRepository,
    AIAuditLogRepository,
)

__all__ = [
    "BaseRepository",
    "SupplyIntelligenceRunRepository",
    "SupplierPerformanceRepository",
    "ReplenishmentRecommendationRepository",
    "LogisticsIntelligenceRunRepository",
    "CarrierPerformanceRepository",
    "LanePerformanceRepository",
    "ShipmentEvaluationRepository",
    "NetworkFlowRunRepository",
    "NetworkNodeSnapshotRepository",
    "NetworkEdgeSnapshotRepository",
    "NetworkRiskSnapshotRepository",
    "NetworkOptimizationRunRepository",
    "NetworkIntelligenceRunRepository",
    "NetworkRiskEventRepository",
    "FinancialIntelligenceRunRepository",
    "FinancialBaselineSnapshotRepository",
    "ScenarioRunRepository",
    "ScenarioMetricSnapshotRepository",
    "IntelligenceRunRepository",
    "CapabilityStateRepository",
    "IntelligenceSnapshotRepository",
    "BusinessSignalRepository",
    "PrioritizedActionRepository",
    "ConversationRepository",
    "ConversationMessageRepository",
    "AIAuditLogRepository",
]