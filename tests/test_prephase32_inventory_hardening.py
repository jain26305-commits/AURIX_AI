from aurix_core.inventory.config import InventoryConfiguration
from aurix_core.inventory.gate import InventoryReadinessGate
from aurix_core.inventory.orchestrator import Phase4Orchestrator


def _phase3_output():
    return {
        "run_id": "A4-INVENTORY-HARDENING",
        "timestamp": "2026-08-27T00:00:00",
        "portfolio_summary": {"total_skus": 1},
        "sku_forecasts": {
            "SKU-A4-001": {
                "entity_id": "SKU-A4-001",
                "forecast_status": "FORECAST_AVAILABLE",
                "champion_model": "XGBOOST",
                "forecast_horizon": 1,
                "forecast": [
                    {
                        "date": "2026-08-27",
                        "point_forecast": 10.0,
                        "raw_model_forecast": 10.0,
                        "constraint_applied": False,
                        "constraint_reason": None,
                        "lower_bound": 8.0,
                        "upper_bound": 12.0,
                        "interval_status": "COMPUTED",
                    }
                ],
                "selection_reason": "AURIX_A4",
                "baseline_model": "NAIVE",
                "model_competition": [],
                "data_quality_flags": [],
                "limitations": [],
                "provenance": {
                    "phase3_run_id": "A4-P3",
                    "dataset_hash": "A4-INVENTORY",
                },
            }
        },
    }


def test_negative_on_hand_is_rejected():
    ready, issues = InventoryReadinessGate.evaluate(
        {
            "lead_time_days": 7,
            "expected_daily_demand": 10,
            "unit_cost": 20,
            "on_hand_qty": -1,
        }
    )

    assert ready is False
    assert any(
        issue["field"] == "on_hand_qty"
        and issue["state"] == "INVALID_INPUT"
        for issue in issues
    )


def test_nan_on_hand_is_rejected():
    ready, issues = InventoryReadinessGate.evaluate(
        {
            "lead_time_days": 7,
            "expected_daily_demand": 10,
            "unit_cost": 20,
            "on_hand_qty": float("nan"),
        }
    )

    assert ready is False
    assert any(
        issue["field"] == "on_hand_qty"
        and issue["state"] == "INVALID_INPUT"
        for issue in issues
    )


def test_negative_lead_time_is_rejected():
    ready, issues = InventoryReadinessGate.evaluate(
        {
            "lead_time_days": -1,
            "expected_daily_demand": 10,
            "unit_cost": 20,
        }
    )

    assert ready is False
    assert any(
        issue["field"] == "lead_time_days"
        and issue["state"] == "INVALID_INPUT"
        for issue in issues
    )


def test_negative_demand_is_rejected():
    ready, issues = InventoryReadinessGate.evaluate(
        {
            "lead_time_days": 7,
            "expected_daily_demand": -10,
            "unit_cost": 20,
        }
    )

    assert ready is False
    assert any(
        issue["field"] == "expected_daily_demand"
        and issue["state"] == "INVALID_INPUT"
        for issue in issues
    )


def test_negative_unit_cost_is_rejected():
    ready, issues = InventoryReadinessGate.evaluate(
        {
            "lead_time_days": 7,
            "expected_daily_demand": 10,
            "unit_cost": -20,
        }
    )

    assert ready is False
    assert any(
        issue["field"] == "unit_cost"
        and issue["state"] == "INVALID_INPUT"
        for issue in issues
    )


def test_missing_on_hand_does_not_become_zero():
    result = Phase4Orchestrator(
        _phase3_output(),
        user_inputs={
            "SKU-A4-001": {
                "lead_time_days": 7,
                "unit_cost": 20,
            }
        },
    ).execute()

    sku = result["sku_inventory_intelligence"]["SKU-A4-001"]

    assert sku["status"] == "COMPUTABLE"
    assert sku["risk_status"] == "NOT_ASSESSABLE"

    assert "ON_HAND_INVENTORY_UNAVAILABLE" in sku["limitations"]

    assert sku["metrics"]["inventory_position"]["value"] is None
    assert sku["metrics"]["inventory_position"]["state"] == "UNAVAILABLE"

    assert sku["metrics"]["inventory_coverage_days"]["value"] is None
    assert sku["metrics"]["inventory_coverage_days"]["state"] == "UNAVAILABLE"

    assert sku["financials"]["inventory_value"]["value"] is None


def test_explicit_zero_on_hand_remains_valid_observation():
    result = Phase4Orchestrator(
        _phase3_output(),
        user_inputs={
            "SKU-A4-001": {
                "lead_time_days": 7,
                "unit_cost": 20,
                "on_hand_qty": 0,
                "inbound_qty": 0,
                "committed_qty": 0,
            }
        },
    ).execute()

    sku = result["sku_inventory_intelligence"]["SKU-A4-001"]

    assert sku["status"] == "COMPUTABLE"

    assert sku["metrics"]["inventory_position"]["value"] == 0.0
    assert sku["metrics"]["inventory_position"]["state"] == "DERIVED"

    assert sku["financials"]["inventory_value"]["value"] == 0.0


def test_invalid_service_level_below_supported_range_fails_closed():
    result = Phase4Orchestrator(
        _phase3_output(),
        user_inputs={
            "SKU-A4-001": {
                "lead_time_days": 7,
                "unit_cost": 20,
                "on_hand_qty": 50,
                "service_level": 0.80,
            }
        },
    ).execute()

    sku = result["sku_inventory_intelligence"]["SKU-A4-001"]

    assert sku["status"] == "USER_INPUT_REQUIRED"
    assert sku["risk_status"] == "NOT_ASSESSABLE"
    assert "INVALID_SERVICE_LEVEL" in sku["limitations"]


def test_invalid_service_level_above_supported_range_fails_closed():
    result = Phase4Orchestrator(
        _phase3_output(),
        user_inputs={
            "SKU-A4-001": {
                "lead_time_days": 7,
                "unit_cost": 20,
                "on_hand_qty": 50,
                "service_level": 1.50,
            }
        },
    ).execute()

    sku = result["sku_inventory_intelligence"]["SKU-A4-001"]

    assert sku["status"] == "USER_INPUT_REQUIRED"
    assert sku["risk_status"] == "NOT_ASSESSABLE"
    assert "INVALID_SERVICE_LEVEL" in sku["limitations"]


def test_nan_service_level_fails_closed():
    result = Phase4Orchestrator(
        _phase3_output(),
        user_inputs={
            "SKU-A4-001": {
                "lead_time_days": 7,
                "unit_cost": 20,
                "on_hand_qty": 50,
                "service_level": float("nan"),
            }
        },
    ).execute()

    sku = result["sku_inventory_intelligence"]["SKU-A4-001"]

    assert sku["status"] == "USER_INPUT_REQUIRED"
    assert sku["risk_status"] == "NOT_ASSESSABLE"
    assert "INVALID_SERVICE_LEVEL" in sku["limitations"]


def test_optional_inbound_quantity_negative_is_rejected():
    ready, issues = InventoryReadinessGate.evaluate(
        {
            "lead_time_days": 7,
            "expected_daily_demand": 10,
            "unit_cost": 20,
            "inbound_qty": -5,
        }
    )

    assert ready is False
    assert any(
        issue["field"] == "inbound_qty"
        and issue["state"] == "INVALID_INPUT"
        for issue in issues
    )


def test_optional_committed_quantity_negative_is_rejected():
    ready, issues = InventoryReadinessGate.evaluate(
        {
            "lead_time_days": 7,
            "expected_daily_demand": 10,
            "unit_cost": 20,
            "committed_qty": -5,
        }
    )

    assert ready is False
    assert any(
        issue["field"] == "committed_qty"
        and issue["state"] == "INVALID_INPUT"
        for issue in issues
    )


def test_valid_z_score_mapping_remains_unchanged():
    assert InventoryConfiguration.get_z_score(0.95) == 1.645
    assert InventoryConfiguration.get_z_score(0.99) == 2.326
