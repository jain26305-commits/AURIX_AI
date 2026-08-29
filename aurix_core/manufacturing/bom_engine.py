"""
AURIX Manufacturing & Production Intelligence — Multi-Level BOM Explosion Engine
Phase 23 Core Implementation.
Recursively explodes N-level BOMs with cumulative multipliers, scrap factors, and circular loop protection.
"""

from __future__ import annotations

from typing import Any, Dict, List, Set
from aurix_core.manufacturing.contracts import (
    BOMExplodedComponent,
    BOMExplosionResult,
)


class BOMExplosionEngine:
    """Recursive Multi-Level Bill of Materials explosion engine."""

    @classmethod
    def explode_bom(
        cls,
        parent_sku_id: str,
        target_quantity: float,
        bom_relationships: List[Dict[str, Any]],
        products_lookup: Dict[str, Dict[str, Any]] | None = None,
        max_depth: int = 10,
    ) -> BOMExplosionResult:
        """
        Recursively explodes a multi-level BOM into flat required components.
        Calculates cumulative requirements: Q_req = Q_parent * Multiplier * (1 + ScrapFactor).
        Protects against infinite recursion via circular reference detection.
        """
        lookup = products_lookup or {}
        # Group BOM lines by parent SKU
        bom_tree: Dict[str, List[Dict[str, Any]]] = {}
        for line in bom_relationships:
            p_id = str(line.get("parent_sku_id"))
            if p_id not in bom_tree:
                bom_tree[p_id] = []
            bom_tree[p_id].append(line)

        exploded_components: List[BOMExplodedComponent] = []
        max_depth_reached = 0

        def _recurse(
            current_parent: str,
            current_multiplier: float,
            current_level: int,
            visited_path: Set[str],
        ):
            nonlocal max_depth_reached
            if current_level > max_depth:
                return
            if current_level > max_depth_reached:
                max_depth_reached = current_level

            children = bom_tree.get(current_parent, [])
            for child in children:
                c_id = str(child.get("component_sku_id"))
                if c_id in visited_path:
                    raise ValueError(f"Circular BOM dependency detected: {visited_path} -> {c_id}")

                qty_required = float(child.get("quantity_required") or 1.0)
                scrap_factor = float(child.get("scrap_factor") or 0.0)
                uom = str(child.get("unit_of_measure") or "PCS")

                effective_multiplier = current_multiplier * qty_required * (1.0 + scrap_factor)
                total_qty = round(target_quantity * effective_multiplier, 4)

                c_info = lookup.get(c_id, {})
                c_name = str(c_info.get("name") or c_info.get("sku_code") or c_id)
                lead_time = float(c_info.get("lead_time_days") or 0.0)

                exploded_components.append(
                    BOMExplodedComponent(
                        component_sku_id=c_id,
                        component_name=c_name,
                        level=current_level,
                        parent_sku_id=current_parent,
                        quantity_per_parent=qty_required,
                        scrap_factor=scrap_factor,
                        cumulative_multiplier=round(effective_multiplier, 6),
                        total_required_quantity=total_qty,
                        unit_of_measure=uom,
                        lead_time_days=lead_time,
                    )
                )

                # Recursive descent if child itself is an intermediate sub-assembly
                if c_id in bom_tree:
                    _recurse(c_id, effective_multiplier, current_level + 1, visited_path | {c_id})

        _recurse(parent_sku_id, 1.0, 1, {parent_sku_id})

        return BOMExplosionResult(
            parent_sku_id=parent_sku_id,
            target_production_quantity=target_quantity,
            max_depth_reached=max_depth_reached,
            total_components_count=len(exploded_components),
            components=exploded_components,
        )
