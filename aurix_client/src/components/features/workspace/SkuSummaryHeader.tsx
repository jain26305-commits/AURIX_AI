'use client';

import React from 'react';
import { SkuUnifiedStory } from '@/types/sku-workspace.types';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { Sparkles } from 'lucide-react';

interface SkuSummaryHeaderProps {
  story: SkuUnifiedStory;
}

export const SkuSummaryHeader: React.FC<SkuSummaryHeaderProps> = ({ story }) => {
  const { demand, inventory, forecast } = story;

  return (
    <div className="space-y-4">
      {/* Top Natural Language Executive Summary */}
      <div className="p-4 rounded-xl bg-gold/[0.04] border border-gold/25 flex items-start gap-3 text-xs font-mono leading-relaxed">
        <Sparkles className="w-4 h-4 text-gold shrink-0 mt-0.5" />
        <div>
          <span className="text-gold font-bold block mb-0.5">AURIX 360° SYNTHESIS:</span>
          <span className="text-slate-200">{story.naturalLanguageSummary}</span>
        </div>
      </div>

      {/* 4 Macro KPI Pillars */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs font-mono">
        <AurixCard title="CLASSIFICATION" badge={<AurixBadge variant="gold">{demand.abcClass}-{demand.xyzClass}</AurixBadge>}>
          <div className="text-xl font-bold text-white mt-1">{demand.demandPattern} Pattern</div>
          <div className="text-[10px] text-slate-500 mt-0.5">CV Volatility: {(demand.coefficientOfVariation * 100).toFixed(0)}%</div>
        </AurixCard>

        <AurixCard title="CHAMPION MODEL" badge={<AurixBadge variant="info">{forecast.metadata.confidenceScorePercent}% CONF</AurixBadge>}>
          <div className="text-xl font-bold text-white mt-1 truncate">{forecast.metadata.modelFamily}</div>
          <div className="text-[10px] text-slate-500 mt-0.5">Error: {forecast.metadata.accuracyWape}% WAPE</div>
        </AurixCard>

        <AurixCard title="STOCK POSITION" badge={<AurixBadge variant={inventory.daysOfCoverRemaining <= 15 ? 'danger' : 'success'}>{inventory.daysOfCoverRemaining}d COVER</AurixBadge>}>
          <div className="text-xl font-bold text-white mt-1">{inventory.currentStockUnits} pcs</div>
          <div className="text-[10px] text-slate-500 mt-0.5">ROP Trigger: {inventory.reorderPointUnits} pcs (SS: {inventory.safetyStockUnits}u)</div>
        </AurixCard>

        <AurixCard title="CAPITAL EXPOSURE" badge={<AurixBadge variant="warning">INR</AurixBadge>}>
          <div className="text-xl font-bold text-gold mt-1">₹{(inventory.capitalTiedUpINR / 1000).toFixed(1)}k</div>
          <div className="text-[10px] text-slate-500 mt-0.5">At Risk: ₹{(inventory.stockoutRevenueAtRiskINR / 1000).toFixed(1)}k</div>
        </AurixCard>
      </div>
    </div>
  );
};