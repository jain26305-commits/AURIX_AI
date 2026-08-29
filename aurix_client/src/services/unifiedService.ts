import { ApiClient } from "@/services/api/apiClient";

export interface UnifiedOverviewDTO {
  healthScorePct: number;
  totalWorkingCapitalUsd: number;
  revenueAtRiskUsd: number;
  realizedValueUsd: number;
  criticalAlertsCount: number;
  pendingApprovalsCount: number;
  activeAgentsCount: number;
}

export class UnifiedService {
  public static async getPanoramicOverview(): Promise<UnifiedOverviewDTO> {
    return ApiClient.get<UnifiedOverviewDTO>("/analytics/overview", () => ({
      healthScorePct: 96.8,
      totalWorkingCapitalUsd: 14500000.0,
      revenueAtRiskUsd: 320000.0,
      realizedValueUsd: 1250000.0,
      criticalAlertsCount: 2,
      pendingApprovalsCount: 3,
      activeAgentsCount: 4,
    }));
  }

  public static async getDemandAnalytics(): Promise<any> {
    return ApiClient.get("/demand", () => ({
      status: "COMPUTED",
      classified_skus: {
        "SKU-PUMP-01": { pattern: "SMOOTH", cv2: 0.12, adi: 1.1 },
        "SKU-VALVE-04": { pattern: "ERRATIC", cv2: 0.54, adi: 1.3 },
      },
    }));
  }

  public static async getInventoryAnalytics(): Promise<any> {
    return ApiClient.get("/inventory", () => ({
      status: "COMPUTED",
      inventory_policies: {
        "SKU-MOTOR-01": { safety_stock: 300, rop: 450 },
      },
    }));
  }

  public static async getSupplyAnalytics(): Promise<any> {
    return ApiClient.get("/supply", () => ({
      status: "COMPUTED",
      supplier_performance: {
        "Precision Parts Ltd": { otd_pct: 99.4, quality_rating: 4.9 },
      },
    }));
  }

  public static async getLogisticsAnalytics(): Promise<any> {
    return ApiClient.get("/logistics", () => ({
      status: "COMPUTED",
      shipments: {
        "SHP-8801": { carrier: "DHL Freight", status: "ON_SCHEDULE" },
      },
    }));
  }

  public static async getEconomicsAnalytics(): Promise<any> {
    return ApiClient.get("/economics", () => ({
      status: "COMPUTED",
      portfolio_working_capital: 14500000.0,
      portfolio_annual_holding_cost: 2900000.0,
    }));
  }
}
