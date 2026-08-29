import { ApiClient } from '@/services/api/apiClient';
import {
  InventoryAnalyticsReport,
  InventoryPolicyRecalculateRequest,
  InventoryPolicyRecalculateResponse,
} from '@/types/inventory.types';
import { InventoryAdapter } from '@/services/adapters/inventoryAdapter';

export class InventoryService {
  public static async fetchInventoryAnalytics(): Promise<InventoryAnalyticsReport> {
    return ApiClient.get<InventoryAnalyticsReport>(
      '/inventory',
      () => InventoryAdapter.generateSimulatedInventory()
    );
  }

  public static async recalculatePolicy(
    req: InventoryPolicyRecalculateRequest
  ): Promise<InventoryPolicyRecalculateResponse> {
    return ApiClient.post<
      InventoryPolicyRecalculateRequest,
      InventoryPolicyRecalculateResponse
    >(
      '/inventory/recalculate-policy',
      req,
      () => {
        const inventory = InventoryAdapter.generateSimulatedInventory().skuInventories.find(
          (s) => s.skuId === req.skuId
        );

        if (!inventory) {
          throw new Error('SKU not found for policy recalculation.');
        }

        // Z-Score mapping based on requested cycle service level
        const zScore =
          req.serviceLevelTargetPercent >= 99 ? 2.33 :
          req.serviceLevelTargetPercent >= 98 ? 2.05 :
          req.serviceLevelTargetPercent >= 95 ? 1.65 : 1.28;

        // Baseline Z-Score used in current inventory state
        const baseZ =
          inventory.serviceLevelTargetPercent >= 99 ? 2.33 :
          inventory.serviceLevelTargetPercent >= 98 ? 2.05 :
          inventory.serviceLevelTargetPercent >= 95 ? 1.65 : 1.28;

        // Proportional standard deviation scaling based on Z-Score ratio
        const computedSafetyStockUnits = Math.round((inventory.safetyStockUnits / baseZ) * zScore);
        const leadTimeDemandUnits = Math.round(inventory.averageDailyDemand * inventory.leadTimeDaysUsed);
        const computedReorderPointUnits = leadTimeDemandUnits + computedSafetyStockUnits;

        return {
          skuId: req.skuId,
          serviceLevelTargetPercent: req.serviceLevelTargetPercent,
          computedSafetyStockUnits,
          computedReorderPointUnits,
          leadTimeDemandUnits,
          zScoreUsed: zScore,
          stockoutProbabilityPercent: Math.max(0.1, 100 - req.serviceLevelTargetPercent),
          recommendationAction: `Adjusted inventory policy for ${req.serviceLevelTargetPercent}% SLA requires ${computedSafetyStockUnits} units of safety buffer.`,
        };
      }
    );
  }
}
