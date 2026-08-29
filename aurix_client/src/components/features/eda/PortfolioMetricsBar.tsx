'use client';

import React from 'react';
import { PortfolioSummaryMetrics } from '@/types/eda.types';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { Package, TrendingUp, DollarSign, Activity } from 'lucide-react';

interface PortfolioMetricsBarProps {
  summary: PortfolioSummaryMetrics;
}

export const PortfolioMetricsBar: React.FC<PortfolioMetricsBarProps> = ({ summary }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      <AurixCard
        title="PORTFOLIO VOLUME"
        badge={<AurixBadge variant="info">ANNUAL</AurixBadge>}
      >
        <div className="flex items-baseline justify-between mt-2">
          <span className="text-2xl font-bold font-mono text-white">
            {summary.totalAnnualVolume.toLocaleString()} <span className="text-xs text-slate-500">pcs</span>
          </span>
          <Package className="w-5 h-5 text-[#D4AF37]" />
        </div>
        <div className="text-[11px] font-mono text-slate-400 mt-1">
          Active Material Base: <span className="text-white font-bold">{summary.totalSkus} SKUs</span>
        </div>
      </AurixCard>

      <AurixCard
        title="REALIZED VALUE"
        badge={<AurixBadge variant="gold">PORTFOLIO</AurixBadge>}
      >
        <div className="flex items-baseline justify-between mt-2">
          <span className="text-2xl font-bold font-mono text-gold">
            ₹{(summary.totalAnnualRevenueINR / 100000).toFixed(1)}L
          </span>
          <DollarSign className="w-5 h-5 text-gold" />
        </div>
        <div className="text-[11px] font-mono text-slate-400 mt-1">
          Revenue Concentration: <span className="text-[#3DDB91] font-bold">Pareto Verified</span>
        </div>
      </AurixCard>

      <AurixCard
        title="MEAN DEMAND CV"
        badge={<AurixBadge variant="warning">VOLATILITY</AurixBadge>}
      >
        <div className="flex items-baseline justify-between mt-2">
          <span className="text-2xl font-bold font-mono text-[#F3B33D]">
            {(summary.portfolioMeanCV * 100).toFixed(1)}%
          </span>
          <Activity className="w-5 h-5 text-[#F3B33D]" />
        </div>
        <div className="text-[11px] font-mono text-slate-400 mt-1">
          Class X (Stable): <span className="text-white font-bold">{summary.xyzDistribution.classX} SKUs</span>
        </div>
      </AurixCard>

      <AurixCard
        title="INTERMITTENCY"
        badge={<AurixBadge variant={summary.intermittentSkuCount > 0 ? 'warning' : 'success'}>SPARSE</AurixBadge>}
      >
        <div className="flex items-baseline justify-between mt-2">
          <span className="text-2xl font-bold font-mono text-white">
            {summary.intermittentSkuCount} <span className="text-xs text-slate-500">SKUs</span>
          </span>
          <TrendingUp className="w-5 h-5 text-[#D4AF37]" />
        </div>
        <div className="text-[11px] font-mono text-slate-400 mt-1">
          Croston / TSB routing enabled
        </div>
      </AurixCard>
    </div>
  );
};