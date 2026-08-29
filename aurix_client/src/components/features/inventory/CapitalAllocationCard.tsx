'use client';

import React, { useMemo } from 'react';
import { SkuInventoryMetrics } from '@/types/inventory.types';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { Landmark } from 'lucide-react';

interface CapitalAllocationCardProps {
  skuInventories: SkuInventoryMetrics[];
}

export const CapitalAllocationCard: React.FC<CapitalAllocationCardProps> = ({ skuInventories }) => {
  const ranked = useMemo(
    () => [...skuInventories].sort((a, b) => b.capitalTiedUpINR - a.capitalTiedUpINR).slice(0, 8),
    [skuInventories]
  );
  const maxCapital = Math.max(...ranked.map((s) => s.capitalTiedUpINR), 1);
  const totalExcess = skuInventories.reduce((sum, s) => sum + s.excessCapitalExposureINR, 0);

  return (
    <AurixCard
      title="HOLDING COST & WORKING CAPITAL DECOMPOSITION"
      badge={<AurixBadge variant="warning">₹{(totalExcess / 100000).toFixed(1)}L EXCESS</AurixBadge>}
    >
      <div className="space-y-2.5 pt-2 font-mono text-xs">
        {ranked.map((sku) => (
          <div key={sku.skuId}>
            <div className="flex justify-between mb-1">
              <span className="text-slate-300 truncate flex items-center gap-1.5">
                <Landmark className="w-3 h-3 text-gold shrink-0" />
                {sku.skuName}
              </span>
              <span className="text-white font-bold">₹{(sku.capitalTiedUpINR / 100000).toFixed(2)}L</span>
            </div>
            <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-gold/50 to-gold rounded-full"
                style={{ width: `${Math.round((sku.capitalTiedUpINR / maxCapital) * 100)}%` }}
              />
            </div>
            {sku.excessCapitalExposureINR > 0 && (
              <div className="text-[10px] text-[#F3B33D] mt-0.5">
                ₹{(sku.excessCapitalExposureINR / 100000).toFixed(2)}L above optimal carrying threshold
              </div>
            )}
          </div>
        ))}
      </div>
    </AurixCard>
  );
};
