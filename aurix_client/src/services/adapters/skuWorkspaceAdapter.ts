import { SkuUnifiedStory } from '@/types/sku-workspace.types';
import { EdaAdapter } from '@/services/adapters/edaAdapter';
import { ForecastAdapter } from '@/services/adapters/forecastAdapter';
import { InventoryAdapter } from '@/services/adapters/inventoryAdapter';
import { SupplyAdapter } from '@/services/adapters/supplyAdapter';
import { IntelligenceAdapter } from '@/services/adapters/intelligenceAdapter';

export class SkuWorkspaceAdapter {
  public static generateUnifiedSkuStory(skuId: string = 'SKU-001'): SkuUnifiedStory {
    const eda = EdaAdapter.generateSimulatedEda();
    const forecast = ForecastAdapter.generateSimulatedForecast(skuId, '3M');
    const inventory = InventoryAdapter.generateSimulatedInventory();
    const supply = SupplyAdapter.generateSimulatedSupply();
    const recommendations = IntelligenceAdapter.generateSimulatedRecommendations();

    const demandProfile = eda.skuProfiles.find((s) => s.skuId === skuId) || eda.skuProfiles[0];
    const inventoryMetrics = inventory.skuInventories.find((s) => s.skuId === skuId) || inventory.skuInventories[0];
    const primarySupplier = supply.suppliers[0];
    const skuRecommendations = recommendations.recommendations.filter((r) => r.targetSkuId === skuId);

    const isCritical = inventoryMetrics.healthStatus === 'CRITICAL_BREACH';
    const isWatch = inventoryMetrics.healthStatus === 'RISK_OF_STOCKOUT' || inventoryMetrics.healthStatus === 'EXCESS_INVENTORY';

    const healthStatus: 'OPTIMAL' | 'WATCH' | 'CRITICAL' = isCritical ? 'CRITICAL' : isWatch ? 'WATCH' : 'OPTIMAL';

    const naturalLanguageSummary =
      skuId === 'SKU-004'
        ? 'SKU-004 is projecting an imminent stockout breach within 6 days due to seasonal surge and supplier turnaround variance. An Air Freight expedite of 300 units is prescribed.'
        : skuId === 'SKU-005'
        ? 'SKU-005 holds 331 days of excess inventory tying up ₹2.13L in working capital. A 15% promotional liquidation and PO freeze is advised.'
        : 'SKU-001 operates in steady-state balance with 83 days of forward cover, optimal XGBoost forecast convergence (91.8%), and stable vendor performance.';

    return {
      skuId: demandProfile.skuId,
      skuName: demandProfile.skuName,
      category: demandProfile.category,
      evaluatedAt: new Date().toISOString(),
      overallHealthStatus: healthStatus,
      naturalLanguageSummary,
      demand: demandProfile,
      forecast: {
        metadata: forecast.metadata,
        timeline: forecast.timeline,
      },
      inventory: inventoryMetrics,
      supplier: primarySupplier,
      activeRecommendations: skuRecommendations,
    };
  }
}