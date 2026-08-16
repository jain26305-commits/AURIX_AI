"""Comprehensive Unit, Integration, and Persistence Test Suite for Phase 7 Network Intelligence."""

import unittest
from typing import Any, Dict
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Database & Engine Imports
from aurix_core.database.engine import Base
from aurix_core.database.models import (
    forecasting,
    ingestion,
    inventory_intelligence,
    logistics_intelligence,
    network_intelligence,
    supply_chain,
    supply_intelligence,
)
from aurix_core.database.repositories.network_intelligence import (
    NetworkIntelligenceRunRepository,
    NetworkNodeSnapshotRepository,
)

# Network Intelligence Core & Service Imports
from aurix_core.network.orchestrator import Phase7AOrchestrator
from aurix_core.network.service import NetworkIntelligenceService
from aurix_core.network.topology import NetworkTopologyBuilder


class TestPhase7ANetwork(unittest.TestCase):
    """Unit and analytical domain test cases for Phase 7 Network Intelligence."""

    def test_01_node_type_parsing_and_identity(self) -> None:
        """Test node type parsing and alias normalization."""
        self.assertEqual(NetworkTopologyBuilder.parse_node_type("VENDOR"), "SUPPLIER")
        self.assertEqual(NetworkTopologyBuilder.parse_node_type("DC"), "DISTRIBUTION_CENTER")

        node_id = "SUPP-01"
        node_type = NetworkTopologyBuilder.parse_node_type("SUPPLIER")
        identity = NetworkTopologyBuilder.build_node_identity(
            node_id=node_id,
            node_type=node_type,
            name="Apex Supplier",
            capacity_units=1000.0,
            inventory_units=200.0,
        )
        self.assertEqual(identity.node_id, "SUPP-01")
        self.assertEqual(identity.capacity.value, 1000.0)

    def test_02_network_edge_creation_and_flow(self) -> None:
        """Test directed edge creation and flow tracking."""
        edge = NetworkTopologyBuilder.build_network_edge(
            source_id="SUPP-01",
            destination_id="WH-01",
            sku_id="SKU-NET-01",
            flow_quantity=500.0,
            lead_time_days=3.0,
            cost=150.0,
        )
        self.assertEqual(edge.source_node_id, "SUPP-01")
        self.assertEqual(edge.destination_node_id, "WH-01")
        self.assertEqual(edge.flow_quantity.value, 500.0)

    def test_03_topology_cycle_detection_and_connectivity(self) -> None:
        """Test DFS cycle detection and orphan node validation."""
        edge1 = NetworkTopologyBuilder.build_network_edge("A", "B", "SKU-1", 100.0)
        edge2 = NetworkTopologyBuilder.build_network_edge("B", "C", "SKU-1", 100.0)
        edge3 = NetworkTopologyBuilder.build_network_edge("C", "A", "SKU-1", 100.0)

        cycles = NetworkTopologyBuilder.detect_cycles([edge1, edge2, edge3])
        self.assertTrue(len(cycles) > 0)

        nodes = {
            "A": NetworkTopologyBuilder.build_node_identity(
                "A", NetworkTopologyBuilder.parse_node_type("PLANT")
            ),
            "B": NetworkTopologyBuilder.build_node_identity(
                "B", NetworkTopologyBuilder.parse_node_type("DC")
            ),
            "ORPHAN": NetworkTopologyBuilder.build_node_identity(
                "ORPHAN", NetworkTopologyBuilder.parse_node_type("WAREHOUSE")
            ),
        }
        orphans, missing_src, missing_dst = NetworkTopologyBuilder.validate_connectivity(
            nodes, [edge1]
        )
        self.assertIn("ORPHAN", orphans)

    def test_10_orchestrator_end_to_end_portfolio_network(self) -> None:
        """Test end-to-end Phase 7A orchestrator execution."""
        payload = {
            "nodes": [
                {
                    "node_id": "SUPP-1",
                    "node_type": "SUPPLIER",
                    "node_name": "Supplier 1",
                    "capacity_units": 1000.0,
                },
                {
                    "node_id": "WH-1",
                    "node_type": "WAREHOUSE",
                    "node_name": "Warehouse 1",
                    "inventory_units": 300.0,
                },
            ],
            "edges": [
                {
                    "source_node_id": "SUPP-1",
                    "destination_node_id": "WH-1",
                    "sku_id": "SKU-1",
                    "flow_quantity": 400.0,
                    "lead_time_days": 2.0,
                }
            ],
        }
        orchestrator = Phase7AOrchestrator(network_data=payload)
        res = orchestrator.execute()
        self.assertEqual(res.get("status"), "COMPUTABLE")
        self.assertEqual(res.get("portfolio_summary", {}).get("total_nodes"), 2)

    def test_11_orchestrator_missing_inputs(self) -> None:
        """Test orchestrator behavior with missing node inputs."""
        orchestrator = Phase7AOrchestrator(network_data={})
        res = orchestrator.execute()
        self.assertEqual(res.get("status"), "USER_INPUT_REQUIRED")


class TestPhase7ANetworkPersistence(unittest.TestCase):
    """Enterprise integration tests verifying database persistence and tenant isolation."""

    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )

        # Register all metadata
        _ = supply_chain.__name__
        _ = ingestion.__name__
        _ = forecasting.__name__
        _ = inventory_intelligence.__name__
        _ = supply_intelligence.__name__
        _ = logistics_intelligence.__name__
        _ = network_intelligence.__name__

        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(
            bind=self.engine, autocommit=False, autoflush=False
        )
        self.db: Session = self.SessionLocal()

        self.tenant_a = "tenant_alpha"
        self.tenant_b = "tenant_beta"

        self.mock_payload: Dict[str, Any] = {
            "nodes": [
                {
                    "node_id": "SUPP-A",
                    "node_type": "SUPPLIER",
                    "node_name": "Supplier A",
                    "capacity_units": 500.0,
                },
                {
                    "node_id": "DC-A",
                    "node_type": "DISTRIBUTION_CENTER",
                    "node_name": "DC A",
                    "inventory_units": 100.0,
                },
            ],
            "edges": [
                {
                    "source_node_id": "SUPP-A",
                    "destination_node_id": "DC-A",
                    "sku_id": "SKU-A",
                    "flow_quantity": 250.0,
                    "lead_time_days": 1.0,
                }
            ],
        }
        self.mock_config: Dict[str, Any] = {"min_sample_size": 3}

    def tearDown(self) -> None:
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_12_network_persistence_and_provenance(self) -> None:
        """Verifies network runs, nodes, edges, and risk events are committed."""
        service = NetworkIntelligenceService(self.db, self.tenant_a)
        res = service.run_network_intelligence(
            self.mock_payload, config=self.mock_config
        )

        self.assertEqual(res.get("status"), "COMPLETED")
        self.assertFalse(res.get("idempotent_hit"))
        self.assertEqual(res.get("node_count"), 2)
        self.assertEqual(res.get("edge_count"), 1)

        run_repo = NetworkIntelligenceRunRepository(self.db, self.tenant_a)
        run_rec = run_repo.get_by_id(str(res.get("network_run_id")))
        self.assertIsNotNone(run_rec)

        node_repo = NetworkNodeSnapshotRepository(self.db, self.tenant_a)
        nodes = node_repo.list_by_run_id(str(res.get("network_run_id")))
        self.assertEqual(len(nodes), 2)

    def test_13_network_tenant_isolation(self) -> None:
        """Adversarial Test: Tenant B cannot query Tenant A's network runs."""
        service_a = NetworkIntelligenceService(self.db, self.tenant_a)
        res_a = service_a.run_network_intelligence(
            self.mock_payload, config=self.mock_config
        )
        run_id_a = str(res_a.get("network_run_id"))

        run_repo_b = NetworkIntelligenceRunRepository(self.db, self.tenant_b)
        node_repo_b = NetworkNodeSnapshotRepository(self.db, self.tenant_b)

        self.assertIsNone(run_repo_b.get_by_id(run_id_a))
        self.assertEqual(len(node_repo_b.list_by_run_id(run_id_a)), 0)

    def test_14_network_run_idempotency(self) -> None:
        """Verifies duplicate payloads return cached run IDs."""
        service = NetworkIntelligenceService(self.db, self.tenant_a)

        res1 = service.run_network_intelligence(
            self.mock_payload, config=self.mock_config
        )
        self.assertFalse(res1.get("idempotent_hit"))

        res2 = service.run_network_intelligence(
            self.mock_payload, config=self.mock_config
        )
        self.assertTrue(res2.get("idempotent_hit"))
        self.assertEqual(res1.get("network_run_id"), res2.get("network_run_id"))


if __name__ == "__main__":
    unittest.main()