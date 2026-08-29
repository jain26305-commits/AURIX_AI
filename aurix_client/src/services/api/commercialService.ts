import { ApiClient } from '@/services/api/apiClient';
import {
  Account360DTO,
  CommercialOTIFDTO,
  CommercialSummaryDTO,
  PVMDecompositionDTO,
} from '@/types/commercial.types';

export class CommercialService {
  public static async getSummary(periodKey: string = 'CURRENT'): Promise<CommercialSummaryDTO> {
    return ApiClient.get<CommercialSummaryDTO>(
      `/commercial/summary?period=${encodeURIComponent(periodKey)}`,
      () => ({
        tenantId: 'GLOBAL',
        periodKey: periodKey,
        grossRevenue: 1250000.0,
        netRevenue: 1215000.0,
        totalOrders: 145,
        averageOrderValue: 8379.31,
        activeCustomersCount: 38,
        dormantCustomersCount: 6,
        commercialOtifPct: 95.8,
        overallDiscountPct: 2.8,
        topGrowthChannel: 'DIRECT',
        activeAnomaliesCount: 1,
        evaluatedAt: new Date().toISOString(),
      })
    );
  }

  public static async getAccounts(periodKey: string = 'CURRENT'): Promise<Account360DTO[]> {
    return ApiClient.get<Account360DTO[]>(
      `/commercial/accounts?period=${encodeURIComponent(periodKey)}`,
      () => [
        { customerId: 'ACC-001', customerName: 'Quidch Retail Group (D2C)', segment: 'DIRECT', paretoTier: 'TIER_A', healthStatus: 'THRIVING', healthScore: 94, lifetimeRevenue: 842000, periodRevenue: 218000, orderCount: 34, averageOrderValue: 6411.76, daysSinceLastOrder: 2, grossMarginPct: 41.2, discountRatePct: 2.1, otifRatePct: 98.8 },
        { customerId: 'ACC-002', customerName: 'Metro Fashion Hub Pvt Ltd', segment: 'WHOLESALE', paretoTier: 'TIER_A', healthStatus: 'STABLE', healthScore: 82, lifetimeRevenue: 615000, periodRevenue: 142000, orderCount: 18, averageOrderValue: 7888.89, daysSinceLastOrder: 6, grossMarginPct: 36.4, discountRatePct: 4.8, otifRatePct: 96.1 },
        { customerId: 'ACC-003', customerName: 'Bright Boulevard Apparel', segment: 'WHOLESALE', paretoTier: 'TIER_A', healthStatus: 'AT_RISK', healthScore: 58, lifetimeRevenue: 398000, periodRevenue: 41000, orderCount: 9, averageOrderValue: 4555.56, daysSinceLastOrder: 34, grossMarginPct: 31.8, discountRatePct: 8.2, otifRatePct: 89.4 },
        { customerId: 'ACC-004', customerName: 'Northgate Department Stores', segment: 'RETAIL_CHAIN', paretoTier: 'TIER_B', healthStatus: 'STABLE', healthScore: 76, lifetimeRevenue: 284000, periodRevenue: 62000, orderCount: 14, averageOrderValue: 4428.57, daysSinceLastOrder: 8, grossMarginPct: 34.9, discountRatePct: 3.6, otifRatePct: 97.2 },
        { customerId: 'ACC-005', customerName: 'Sunrise Textiles Distribution', segment: 'DISTRIBUTOR', paretoTier: 'TIER_B', healthStatus: 'DORMANT', healthScore: 22, lifetimeRevenue: 156000, periodRevenue: 0, orderCount: 0, averageOrderValue: 0, daysSinceLastOrder: 96, grossMarginPct: 0, discountRatePct: 0, otifRatePct: 0 },
        { customerId: 'ACC-006', customerName: 'Quidch Direct Online Store', segment: 'DIRECT', paretoTier: 'TIER_A', healthStatus: 'THRIVING', healthScore: 91, lifetimeRevenue: 512000, periodRevenue: 184000, orderCount: 42, averageOrderValue: 4380.95, daysSinceLastOrder: 1, grossMarginPct: 44.6, discountRatePct: 1.4, otifRatePct: 99.1 },
        { customerId: 'ACC-007', customerName: 'Cascade Regional Boutiques', segment: 'WHOLESALE', paretoTier: 'TIER_C', healthStatus: 'STABLE', healthScore: 68, lifetimeRevenue: 94000, periodRevenue: 12800, orderCount: 4, averageOrderValue: 3200, daysSinceLastOrder: 18, grossMarginPct: 33.1, discountRatePct: 5.4, otifRatePct: 94.8 },
        { customerId: 'ACC-008', customerName: 'Harborline Trading Co.', segment: 'DISTRIBUTOR', paretoTier: 'TIER_C', healthStatus: 'DORMANT', healthScore: 15, lifetimeRevenue: 68000, periodRevenue: 0, orderCount: 0, averageOrderValue: 0, daysSinceLastOrder: 122, grossMarginPct: 0, discountRatePct: 0, otifRatePct: 0 },
      ]
    );
  }

  public static async getOtif(periodKey: string = 'CURRENT'): Promise<CommercialOTIFDTO> {
    return ApiClient.get<CommercialOTIFDTO>(
      `/commercial/otif?period=${encodeURIComponent(periodKey)}`,
      () => ({
        tenantId: 'GLOBAL',
        periodKey: periodKey,
        totalOrders: 145,
        otifOrders: 139,
        otifRatePct: 95.8,
        fillRatePct: 97.6,
        averageLeadTimeDays: 4.2,
        backlogOrderCount: 6,
        cancellationRatePct: 1.4,
      })
    );
  }

  public static async getPvm(periodKey: string = 'CURRENT'): Promise<PVMDecompositionDTO> {
    return ApiClient.get<PVMDecompositionDTO>(
      `/commercial/pvm?period=${encodeURIComponent(periodKey)}`,
      () => ({
        tenantId: 'GLOBAL',
        baselineRevenue: 1120000,
        currentRevenue: 1215000,
        totalRevenueChange: 95000,
        priceEffect: 38000,
        volumeEffect: 52000,
        mixEffect: 5000,
        priceEffectPct: 3.4,
        volumeEffectPct: 4.6,
        mixEffectPct: 0.4,
      })
    );
  }
}
