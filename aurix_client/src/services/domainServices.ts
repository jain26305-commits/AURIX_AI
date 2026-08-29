import { ApiClient } from "@/services/api/apiClient";

export class SupplyChainService {
  public static async getDemandAnalytics(): Promise<any> {
    return ApiClient.get("/demand", () => ({
      status: "COMPUTED",
      classified_skus: {
        "SKU-PUMP-01": { pattern: "SMOOTH", cv2: 0.12, adi: 1.1 },
        "SKU-VALVE-04": { pattern: "ERRATIC", cv2: 0.54, adi: 1.3 },
      },
      total_skus: 2,
    }));
  }

  public static async getForecastAnalytics(): Promise<any> {
    return ApiClient.get("/forecast", () => ({
      status: "COMPUTED",
      sku_forecasts: {
        "SKU-PUMP-01": { point_forecast: 1200, confidence_lower: 1100, confidence_upper: 1300 },
        "SKU-VALVE-04": { point_forecast: 850, confidence_lower: 780, confidence_upper: 920 },
      },
      total_forecasts: 2,
    }));
  }
}

export class InventoryService {
  public static async getInventoryAnalytics(): Promise<any> {
    return ApiClient.get("/inventory", () => ({
      status: "COMPUTED",
      inventory_policies: {
        "SKU-MOTOR-01": { safety_stock: 300, rop: 450, on_hand: 450, status: "HEALTHY" },
        "SKU-BEARING-09": { safety_stock: 100, rop: 120, on_hand: 40, status: "SHORTAGE_RISK" },
      },
      risk_evaluations: {
        "SKU-BEARING-09": { risk_score: 84.5, severity: "HIGH" },
      },
      high_risk_skus_count: 1,
    }));
  }
}

export class CommercialService {
  public static async getCommercialSummary(): Promise<any> {
    return ApiClient.get("/commercial/summary", () => ({
      total_revenue_usd: 24500000.0,
      otif_rate_pct: 98.1,
      discount_leakage_usd: 42000.0,
      customer_accounts: [
        { customer_id: "CUST-APEX", name: "Apex Global Corp", ytd_revenue_usd: 4200000.0, otif_pct: 99.1, pareto_tier: "TIER_A" },
        { customer_id: "CUST-DELTA", name: "Delta Logistics", ytd_revenue_usd: 1850000.0, otif_pct: 96.4, pareto_tier: "TIER_A" },
      ],
    }));
  }
}

export class ManufacturingDomainService {
  public static async getManufacturingSummary(): Promise<any> {
    return ApiClient.get("/manufacturing/summary", () => ({
      overall_oee_pct: 87.4,
      net_requirements_units: 1420,
      primary_bottleneck_station: "Line 4",
      scrap_rate_pct: 1.2,
      active_work_orders: [
        { work_order_id: "WO-9042", sku: "HYDRAULIC_PUMP_V2", target_qty: 500, line: "Line 1 (Antwerp)", status: "IN_PROGRESS" },
        { work_order_id: "WO-9043", sku: "CONTROL_VALVE_ASSEMBLY", target_qty: 350, line: "Line 3 (Munich)", status: "SCHEDULED" },
      ],
    }));
  }
}

export class ProcurementDomainService {
  public static async getSupplyAnalytics(): Promise<any> {
    return ApiClient.get("/supply", () => ({
      status: "COMPUTED",
      supplier_performance: {
        "Precision Parts Ltd": { otd_pct: 99.4, quality_rating: 4.9, annual_spend_usd: 2400000.0, avg_lead_time_days: 12 },
        "Global Steel Works": { otd_pct: 97.8, quality_rating: 4.7, annual_spend_usd: 4100000.0, avg_lead_time_days: 24 },
      },
      supplier_rankings: {
        "Precision Parts Ltd": 1,
        "Global Steel Works": 2,
      },
      high_risk_suppliers_count: 0,
    }));
  }
}

export class LogisticsDomainService {
  public static async getLogisticsAnalytics(): Promise<any> {
    return ApiClient.get("/logistics", () => ({
      status: "COMPUTED",
      shipments: {
        "SHP-8801": { carrier: "DHL Freight", origin: "Plant Antwerp", destination: "DC Munich", status: "ON_SCHEDULE" },
      },
      delayed_shipments_count: 0,
    }));
  }
}

export class RiskDomainService {
  public static async getRiskSummary(): Promise<any> {
    return ApiClient.get("/risk/summary", () => ({
      risk_index: 18.4,
      identified_leakage_usd: 14200.0,
      remediated_threats_count: 12,
      findings: [
        { finding_id: "RSK-001", domain: "PROCUREMENT", exposure_usd: 12400.0, status: "MITIGATED" },
      ],
    }));
  }
}

export class ProcessDomainService {
  public static async getProcessSummary(): Promise<any> {
    return ApiClient.get("/process/summary", () => ({
      o2c_cycle_time_days: 4.2,
      conformance_score_pct: 98.4,
      rework_loops_count: 2,
      process_variants: [
        { variant_name: "Standard PO Approval -> Receipt", instances_count: 1450, avg_cycle_days: 2.1, conformance_pct: 99.1 },
      ],
    }));
  }
}

export class DecisionDomainService {
  public static async getCandidates(): Promise<any[]> {
    return ApiClient.get("/decisions/candidates", () => [
      {
        decision_id: "DEC-PO-SPLIT-101",
        domain: "PROCUREMENT",
        title: "Reallocate PO-4001 Volume to Secondary Certified Supplier",
        why_context: "Port delay in Rotterdam introduces an 8-day supply variance on Hydraulic Seals, threatening assembly line stoppage.",
        options: [
          { option_id: "OPT-A", name: "Split 60/40 with Secondary Vendor (Apex)", expected_value_usd: 42000.0, risk_tier: "LOW", lead_time_days: 2 },
          { option_id: "OPT-B", name: "Expedite Air Freight on Primary PO", expected_value_usd: 18000.0, risk_tier: "MEDIUM", lead_time_days: 1 },
        ],
      },
      {
        decision_id: "DEC-INV-HOLD-102",
        domain: "FINANCE",
        title: "Place Credit Hold on Overdue Account Apex Global",
        why_context: "Outstanding invoice balance exceeds $140,000 at 74 days aging with no receipt confirmation.",
        options: [
          { option_id: "OPT-1", name: "Execute Automatic Shipment Hold", expected_value_usd: 85000.0, risk_tier: "MEDIUM", lead_time_days: 0 },
          { option_id: "OPT-2", name: "Issue 3-Day Payment Demand Notice", expected_value_usd: 45000.0, risk_tier: "LOW", lead_time_days: 3 },
        ],
      },
    ]);
  }
}

export class ScenarioDomainService {
  public static async getScenarioSummary(): Promise<any> {
    return ApiClient.get("/scenarios/summary", () => ({
      simulation_confidence_pct: 98.6,
      monte_carlo_iterations: 10000,
      p90_risk_exposure_usd: 42000.0,
      comparison_rows: [
        { metric: "Contribution Margin", do_nothing: 1200000.0, option_a: 185000.0, option_b: 92000.0, unit: "$" },
        { metric: "Order OTIF Fulfillment", do_nothing: 94.2, option_a: 3.8, option_b: 2.1, unit: "%" },
        { metric: "Inventory Holding Cost", do_nothing: 320000.0, option_a: -45000.0, option_b: -12000.0, unit: "$" },
      ],
    }));
  }
}

export class DataDomainService {
  public static async getConnectors(): Promise<any[]> {
    return ApiClient.get("/data/connectors", () => [
      { system_name: "SAP S/4HANA", connector_type: "OData v4", last_sync: "2m ago", status: "HEALTHY" },
      { system_name: "Odoo ERP", connector_type: "JSON-RPC", last_sync: "5m ago", status: "HEALTHY" },
    ]);
  }
}

export class AdminDomainService {
  public static async getAuditLogs(): Promise<any[]> {
    return ApiClient.get("/admin/audit", () => [
      { log_id: "AUD-9901", actor: "USR-ADMIN-01", action: "DEPLOY_AGENT_VERSION_PROD", timestamp: "2026-08-23T06:00:00Z" },
    ]);
  }
}
