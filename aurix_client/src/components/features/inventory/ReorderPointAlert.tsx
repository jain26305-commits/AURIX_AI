'use client';

import React, { useMemo } from 'react';
import { SkuInventoryMetrics } from '@/types/inventory.types';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { AurixButton } from '@/components/ui/AurixButton';
import { AlertTriangle, PackagePlus } from 'lucide-react';

interface ReorderPointAlertProps {
  skuInventories: SkuInventoryMetrics[];
  onSelectSku?: (skuId: string) => void;
}

export const ReorderPointAlert: React.FC<ReorderPointAlertProps> = ({ skuInventories, onSelectSku }) => {
  const belowRop = useMemo(() => {
    const safeList = Array.isArray(skuInventories) ? skuInventories : [];
    return safeList
      .filter((s) => s.currentStockUnits <= s.reorderPointUnits)
      .sort((a, b) => a.daysOfCoverRemaining - b.daysOfCoverRemaining);
  }, [skuInventories]);

  if (belowRop.length === 0) {
    return (
      <AurixCard title="REORDER POINT BREACH ALERTS" badge={<AurixBadge variant="success">ALL CLEAR</AurixBadge>}>
        <div className="h-24 flex items-center justify-center font-mono text-xs text-slate-500">
          NO SKUs CURRENTLY BELOW REORDER POINT
        </div>
      </AurixCard>
    );
  }

  return (
    <AurixCard
      title="REORDER POINT BREACH ALERTS"
      badge={<AurixBadge variant="danger" pulse>{belowRop.length} SKUs BELOW ROP</AurixBadge>}
    >
      <div className="space-y-2 pt-2 font-mono text-xs">
        {belowRop.map((sku) => (
          <div
            key={sku.skuId}
            className="flex items-center justify-between p-3 rounded-lg bg-[#FF6B6B]/5 border border-[#FF6B6B]/20"
          >
            <div className="flex items-center gap-2.5 min-w-0">
              <AlertTriangle className="w-4 h-4 text-[#FF6B6B] shrink-0" />
              <div className="min-w-0">
                <div className="text-white font-bold truncate">{sku.skuName}</div>
                <div className="text-[10px] text-slate-500">
                  {sku.currentStockUnits} on-hand / ROP {sku.reorderPointUnits} • {sku.daysOfCoverRemaining}d cover left
                </div>
              </div>
            </div>
            <AurixButton variant="secondary" size="sm" onClick={() => onSelectSku?.(sku.skuId)}>
              <PackagePlus className="w-3.5 h-3.5 mr-1.5" /> REVIEW
            </AurixButton>
          </div>
        ))}
      </div>
    </AurixCard>
  );
};
