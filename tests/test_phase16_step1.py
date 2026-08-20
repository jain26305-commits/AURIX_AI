"""Phase 16 Step 1 deterministic-first routing and provider-surface tests."""

from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from aurix_core.database.engine import Base
from aurix_core.database.models.supply_chain import Product, InventoryPosition
from aurix_core.database.models import intelligence as intelligence_models
from aurix_core.intelligence.ai_gateway import AIGateway
from aurix_core.intelligence.router import BusinessRouter, QueryType
from aurix_core.intelligence.service import IntelligenceService
from aurix_core.tools.registry import ToolRegistry


class TestPhase16Step1:
    """Verify deterministic AURIX routing before AI escalation."""

    def setup_method(self) -> None:
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
        )
        _ = intelligence_models.AIAuditLogModel
        Base.metadata.create_all(bind=self.engine)
        self.session_factory = sessionmaker(
            bind=self.engine,
            autoflush=False,
            expire_on_commit=False,
        )
        self.db: Session = self.session_factory()
        self.tenant_id = "tenant-step1"

    def teardown_method(self) -> None:
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_read_router_resolves_deterministic_tool(self) -> None:
        decision = BusinessRouter.route(
            "What is the current inventory for SKU-100?"
        )
        assert decision.query_type == QueryType.READ
        assert decision.requires_ai is False
        assert decision.fast_path_eligible is True
        assert decision.target_capability == "INVENTORY_POSITION_RISK"
        assert decision.target_tool == "inventory.position"

    def test_tool_registry_contains_phase_1_to_15_read_tools(self) -> None:
        names = {item.name for item in ToolRegistry.list_definitions()}
        assert {
            "inventory.position",
            "inventory.replenishment_policy",
            "forecast.latest",
            "supplier.performance",
            "logistics.shipment",
            "intelligence.snapshot",
        }.issubset(names)

    def test_intelligence_service_answers_from_engine_without_ai(self) -> None:
        product = Product(
            id="PROD-100",
            tenant_id=self.tenant_id,
            sku_code="SKU-100",
            name="Test Product",
        )
        self.db.add(product)
        self.db.flush()

        self.db.add(
            InventoryPosition(
                tenant_id=self.tenant_id,
                sku_id=product.id,
                location_id="DC-01",
                on_hand=1200.0,
                on_order=200.0,
                safety_stock=300.0,
                updated_at=datetime.now(timezone.utc),
            )
        )
        self.db.commit()

        response = IntelligenceService(
            self.db,
            self.tenant_id,
        ).ask_ai("What is the current inventory for SKU-100?")

        assert response.answer_source == "AURIX_ENGINE"
        assert response.provider_used == "AURIX_ENGINE"
        assert response.token_usage["total_tokens"] == 0
        assert response.provenance["tool_name"] == "inventory.position"
        assert response.explanation

    def test_ai_gateway_has_only_gemini_and_cloudflare_external_providers(self) -> None:
        gateway = AIGateway()
        assert hasattr(gateway, "flash_lite_provider")
        assert hasattr(gateway, "flash_provider")
        assert hasattr(gateway, "cloudflare_provider")
        provider_names = {
            gateway.flash_lite_provider.provider_name,
            gateway.flash_provider.provider_name,
            gateway.cloudflare_provider.provider_name,
        }
        assert provider_names == {
            "GEMINI_FLASH_LITE",
            "GEMINI_FLASH",
            "CLOUDFLARE",
        }
