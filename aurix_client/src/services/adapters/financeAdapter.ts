import { FinancialExposureReport } from '@/types/finance.types';

export class FinanceAdapter {
  public static generateSimulatedFinancials(): FinancialExposureReport {
    const grossInventory = 2762600;
    const excessDeadStock = 233340;
    const slowMoving = 310000;
    const expeditedFreight = 84500;
    const stockoutLoss = 170700;

    return {
      evaluatedAt: new Date().toISOString(),
      holdingRateAnnualPercent: 22.0,
      metrics: {
        grossInventoryValuationINR: grossInventory,
        healthyCycleStockINR: 1650000,
        safetyBufferCapitalINR: 569260,
        slowMovingCapitalINR: slowMoving,
        excessDeadStockINR: excessDeadStock,
        annualHoldingCostINR: Math.round(grossInventory * 0.22),
        stockoutRevenueLostINR: stockoutLoss,
        expeditedFreightPremiumINR: expeditedFreight,
        unlockedCapitalOpportunityINR: excessDeadStock + Math.round(slowMoving * 0.5),
      },
      waterfallBridge: [
        { category: 'Gross Holding', amountINR: grossInventory, type: 'base', description: 'Total capital currently locked in active warehouse ledger' },
        { category: 'Excess Stock', amountINR: -excessDeadStock, type: 'negative', description: 'Over-stocked variants exceeding 180 days of forward cover' },
        { category: 'Slow Moving', amountINR: -155000, type: 'negative', description: 'Depreciating inventory lines eligible for promotional liquidation' },
        { category: 'Carrying Drag (22%)', amountINR: -133700, type: 'negative', description: 'Warehousing, insurance, and working capital opportunity cost' },
        { category: 'Optimized Target', amountINR: 2240200, type: 'total', description: 'Target operating working capital after AURIX policy execution' },
      ],
    };
  }
}