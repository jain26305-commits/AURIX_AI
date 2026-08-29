'use client';

import React from 'react';
import { SkuInventoryMetrics } from '@/types/inventory.types';
import { AlertOctagon, AlertTriangle } from 'lucide-react';
import { AurixBadge } from '@/components/ui/AurixBadge';

interface StockoutRiskMatrixProps {
  skuInventories: SkuInventoryMetrics[];
  selectedSkuId: string;
  onSelectSku: (id: string) => void;
}

export const StockoutRiskMatrix: React.FC<StockoutRiskMatrixProps> = ({
  skuInventories,
  selectedSkuId,
  onSelectSku,
}) => {
  return (
    <div className="w-full aurix-card-glass rounded-xl p-6 border border-white/[0.08]">
      <div className="flex items-center justify-between pb-4 mb-4 border-b border-white/[0.06]">
        <div>
          <h3 className="text-sm font-semibold text-white tracking-wide flex items-center gap-2">
            <AlertOctagon className="w-4 h-4 text-[#FF6B6B]" />
            STOCKOUT RISK & INVENTORY POSITION MATRIX
          </h3>
          <p className="text-[11px] font-mono text-slate-400 mt-0.5">
            Active buffer health, days of cover, and estimated stockout breach dates.
          </p>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs font-mono">
          <thead>
            <tr className="border-b border-white/[0.08] text-slate-500 text-[10px] uppercase tracking-wider">
              <th className="pb-3 pl-2">SKU Variant</th>
              <th className="pb-3">On Hand</th>
              <th className="pb-3">ROP Trigger</th>
              <th className="pb-3">Days of Cover</th>
              <th className="pb-3">Stockout Prob.</th>
              <th className="pb-3">Breach Timeline</th>
              <th className="pb-3 text-right pr-2">State</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.04]">
            {skuInventories.map((sku) => {
              const isSelected = sku.skuId === selectedSkuId;
              const isCritical = sku.healthStatus === 'CRITICAL_BREACH';
              const isWarning = sku.healthStatus === 'RISK_OF_STOCKOUT';
              const isExcess = sku.healthStatus === 'EXCESS_INVENTORY';

              return (
                <tr
                  key={sku.skuId}
                  onClick={() => onSelectSku(sku.skuId)}
                  className={`cursor-pointer transition-colors ${
                    isSelected ? 'bg-gold/[0.06]' : 'hover:bg-white/[0.02]'
                  }`}
                >
                  <td className="py-3 pl-2">
                    <div className="flex flex-col">
                      <span className={`font-bold ${isSelected ? 'text-gold' : 'text-white'}`}>
                        {sku.skuName}
                      </span>
                      <span className="text-[10px] text-slate-500">{sku.skuId} • {sku.category}</span>
                    </div>
                  </td>

                  <td className="py-3 text-white font-bold">{sku.currentStockUnits} pcs</td>
                  <td className="py-3 text-slate-400">{sku.reorderPointUnits} pcs</td>

                  <td className="py-3">
                    <span className={sku.daysOfCoverRemaining <= 15 ? 'text-[#FF6B6B] font-bold' : 'text-slate-300'}>
                      {sku.daysOfCoverRemaining} Days
                    </span>
                  </td>

                  <td className="py-3">
                    <span className={sku.stockoutProbabilityPercent > 20 ? 'text-[#FF6B6B] font-bold' : 'text-[#3DDB91]'}>
                      {sku.stockoutProbabilityPercent}%
                    </span>
                  </td>

                  <td className="py-3">
                    {sku.stockoutBreachDays ? (
                      <span className="text-[#FF6B6B] font-bold flex items-center gap-1">
                        <AlertTriangle className="w-3.5 h-3.5" /> in {sku.stockoutBreachDays} Days
                      </span>
                    ) : (
                      <span className="text-slate-500 text-[10px]">No Breach</span>
                    )}
                  </td>

                  <td className="py-3 text-right pr-2">
                    {isCritical && <AurixBadge variant="danger" pulse>CRITICAL</AurixBadge>}
                    {isWarning && <AurixBadge variant="warning">WATCH</AurixBadge>}
                    {isExcess && <AurixBadge variant="gold">EXCESS</AurixBadge>}
                    {sku.healthStatus === 'OPTIMAL' && <AurixBadge variant="success">OPTIMAL</AurixBadge>}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};