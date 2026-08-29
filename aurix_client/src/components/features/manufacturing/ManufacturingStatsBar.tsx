'use client';

import React from 'react';

import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { Factory, Layers, AlertOctagon, CheckCircle2 } from 'lucide-react';

export const ManufacturingStatsBar: React.FC<{ summary?: any}> = ({ summary }) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 select-none font-mono">
      <AurixCard title="PLANNED WORK ORDERS" badge={<AurixBadge variant="gold">MRP RUN</AurixBadge>}>
        <div className="flex items-baseline justify-between mt-2">
          <span className="text-2xl font-bold text-white">0{summary.activePlannedOrdersCount} Orders</span>
          <Factory className="w-5 h-5 text-gold" />
        </div>
        <div className="text-[11px] text-slate-400 mt-1">{summary.aggregatePlannedProductionUnits.toLocaleString()} units scheduled</div>
      </AurixCard>

      <AurixCard title="MEAN PLANT YIELD" badge={<AurixBadge variant="success">EFFICIENCY</AurixBadge>}>
        <div className="flex items-baseline justify-between mt-2">
          <span className="text-2xl font-bold text-[#3DDB91]">{summary.meanPlantYieldRatePercent}%</span>
          <CheckCircle2 className="w-5 h-5 text-[#3DDB91]" />
        </div>
        <div className="text-[11px] text-slate-400 mt-1">First-pass quality across lines</div>
      </AurixCard>

      <AurixCard title="WORK CENTER BOTTLENECKS" badge={<AurixBadge variant="danger" pulse>CONSTRAINED</AurixBadge>}>
        <div className="flex items-baseline justify-between mt-2">
          <span className="text-2xl font-bold text-[#FF6B6B]">0{summary.bottleneckWorkCentersCount} Station</span>
          <AlertOctagon className="w-5 h-5 text-[#FF6B6B]" />
        </div>
        <div className="text-[11px] text-slate-400 mt-1">Dyeing vessel utilization at 94.6%</div>
      </AurixCard>

      <AurixCard title="PLANNING CAPACITY" badge={<AurixBadge variant="info">WORK CENTERS</AurixBadge>}>
        <div className="flex items-baseline justify-between mt-2">
          <span className="text-2xl font-bold text-[#D4AF37]">{summary.totalProductionCapacityHours}h</span>
          <Layers className="w-5 h-5 text-[#D4AF37]" />
        </div>
        <div className="text-[11px] text-slate-400 mt-1">Weekly aggregate plant hours</div>
      </AurixCard>
    </div>
  );
};