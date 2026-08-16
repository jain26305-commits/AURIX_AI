"""Compatibility exports for the AURIX Network ORM models.

The canonical Network ORM definitions live in
``aurix_core.database.models.network``.

This module intentionally contains no ORM model declarations. It exists only
to preserve backwards-compatible imports from older Phase 7 code.
"""

from aurix_core.database.models.network import (
    NetworkEdgeSnapshot,
    NetworkFlowRun,
    NetworkIntelligenceRun,
    NetworkNodeSnapshot,
    NetworkOptimizationRun,
    NetworkRiskEvent,
    NetworkRiskSnapshot,
)

__all__ = [
    "NetworkEdgeSnapshot",
    "NetworkFlowRun",
    "NetworkIntelligenceRun",
    "NetworkNodeSnapshot",
    "NetworkOptimizationRun",
    "NetworkRiskEvent",
    "NetworkRiskSnapshot",
]