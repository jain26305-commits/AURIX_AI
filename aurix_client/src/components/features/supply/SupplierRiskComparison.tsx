'use client';

import React, { useMemo } from 'react';
import { SupplierPerformanceProfile } from '@/types/supply.types';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { ShieldAlert, ShieldCheck, Shield } from 'lucide-react';

interface SupplierRiskComparisonProps {
  suppliers: SupplierPerformanceProfile[];
}

export const SupplierRiskComparison: React.FC<SupplierRiskComparisonProps> = ({ suppliers }) => {
  // Sort by delay probability descending
  const rankedVendors = useMemo(() => {
    return [...suppliers].sort((a, b) => b.orderDelayProbabilityPercent - a.orderDelayProbabilityPercent);
  }, [suppliers]);

  const riskBadge: Record<string, 'success' | 'warning' | 'danger'> = {
    LOW: 'success',
    MODERATE: 'warning',
    ELEVATED: 'danger',
    HIGH: 'danger',
  };

  return (
    <AurixCard
      title="SUPPLIER DELIVERY RISK COMPARISON"
      badge={<AurixBadge variant="gold">{rankedVendors.length} VENDORS</AurixBadge>}
    >
      <div className="space-y-2.5 pt-2 font-mono text-xs">
        {rankedVendors.map((v) => {
          const isHighRisk = v.riskLevel === 'ELEVATED' || v.riskLevel === 'HIGH';
          const isLowRisk = v.riskLevel === 'LOW';

          return (
            <div key={v.supplierId} className="flex items-center justify-between p-3 rounded-lg bg-white/[0.02] border border-white/[0.05]">
              <div className="flex items-center gap-2.5 min-w-0">
                {isHighRisk ? (
                  <ShieldAlert className="w-4 h-4 text-[#FF6B6B] shrink-0" />
                ) : isLowRisk ? (
                  <ShieldCheck className="w-4 h-4 text-[#3DDB91] shrink-0" />
                ) : (
                  <Shield className="w-4 h-4 text-[#F3B33D] shrink-0" />
                )}
                <div className="min-w-0">
                  <div className="text-white font-bold truncate">{v.supplierName}</div>
                  <div className="text-[10px] text-slate-500">
                    {v.orderDelayProbabilityPercent}% Delay Prob · {v.qualityDefectPpm} PPM Defect Rate · {v.totalOrdersFulfilled} Historical POs
                  </div>
                </div>
              </div>
              <AurixBadge variant={riskBadge[v.riskLevel] || 'warning'} size="sm">
                {v.riskLevel}
              </AurixBadge>
            </div>
          );
        })}
      </div>
    </AurixCard>
  );
};
