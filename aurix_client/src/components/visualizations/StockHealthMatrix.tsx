'use client';

import React from 'react';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { SkuInventoryMetrics } from '@/types/inventory.types';

export interface StockHealthMatrixProps {
  skuInventories?: SkuInventoryMetrics[];
}

export const StockHealthMatrix: React.FC<StockHealthMatrixProps> = ({ skuInventories = [] }) => {
  if (skuInventories.length === 0) {
    return null;
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {skuInventories.map((item) => {
          const isCritical = item.healthStatus === 'CRITICAL_BREACH';
          const isShortage = item.healthStatus === 'RISK_OF_STOCKOUT';
          const isExcess = item.healthStatus === 'EXCESS_INVENTORY';

          const formatINR = (val: number) => `₹${(val / 100000).toFixed(2)}L`;

          return (
            <AurixCard
              key={item.skuId}
              variant="interactive"
              className={`p-4 space-y-3 ${
                isCritical
                  ? 'border-[#FF6B6B]/40 shadow-[0_0_20px_rgba(255,107,107,0.15)]'
                  : isExcess
                  ? 'border-[#F3B33D]/40 shadow-[0_0_20px_rgba(243,179,61,0.15)]'
                  : 'border-white/[0.06]'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <span className="text-[10px] font-mono font-bold text-[#D4AF37] block truncate">
                    {item.skuId}
                  </span>
                  <h4 className="text-xs font-bold text-white uppercase font-mono truncate max-w-[140px]">
                    {item.skuName}
                  </h4>
                </div>
                <AurixBadge variant={isCritical ? 'danger' : isShortage ? 'warning' : isExcess ? 'gold' : 'success'}>
                  {isCritical ? 'CRITICAL' : isShortage ? 'WATCH' : isExcess ? 'EXCESS' : 'OPTIMAL'}
                </AurixBadge>
              </div>

              <div className="space-y-1.5 pt-2 border-t border-white/[0.04] font-mono text-[11px]">
                <div className="flex justify-between text-slate-400">
                  <span>ON HAND:</span>
                  <span className="text-white font-bold">{item.currentStockUnits.toLocaleString()} units</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>SAFETY STOCK:</span>
                  <span className="text-slate-300">{item.safetyStockUnits.toLocaleString()} units</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>CAPITAL LOCKED:</span>
                  <span className="text-[#D4AF37] font-bold">{formatINR(item.capitalTiedUpINR)}</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>DAYS OF COVER:</span>
                  <span
                    className={
                      item.daysOfCoverRemaining > 90
                        ? 'text-[#F3B33D]'
                        : item.daysOfCoverRemaining <= item.leadTimeDaysUsed
                        ? 'text-[#FF6B6B]'
                        : 'text-slate-300'
                    }
                  >
                    {item.daysOfCoverRemaining} Days
                  </span>
                </div>
              </div>
            </AurixCard>
          );
        })}
      </div>
    </div>
  );
};
