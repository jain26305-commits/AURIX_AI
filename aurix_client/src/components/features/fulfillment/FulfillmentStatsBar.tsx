'use client';

import React from 'react';
import { FulfillmentSummary } from '@/types/fulfillment.types';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { ShoppingBag, CheckCircle2, AlertOctagon, DollarSign } from 'lucide-react';
import { formatINR } from '@/lib/formatters';

export const FulfillmentStatsBar: React.FC<{ summary: FulfillmentSummary }> = ({ summary }) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 select-none font-mono">
      <AurixCard title="ORDER FULFILLMENT RATE" badge={<AurixBadge variant="success">OTIF</AurixBadge>}>
        <div className="flex items-baseline justify-between mt-2">
          <span className="text-2xl font-bold text-[#3DDB91]">{summary.onTimeFulfillmentRatePercent}%</span>
          <CheckCircle2 className="w-5 h-5 text-[#3DDB91]" />
        </div>
        <div className="text-[11px] text-slate-400 mt-1">On-time customer delivery target: 95.0%</div>
      </AurixCard>

      <AurixCard title="ALLOCATED REVENUE" badge={<AurixBadge variant="gold">COMMITTED</AurixBadge>}>
        <div className="flex items-baseline justify-between mt-2">
          <span className="text-2xl font-bold text-gold">{formatINR(summary.allocatedRevenueINR)}</span>
          <DollarSign className="w-5 h-5 text-gold" />
        </div>
        <div className="text-[11px] text-slate-400 mt-1">Across 0{summary.totalOrdersCount} active customer consignments</div>
      </AurixCard>

      <AurixCard title="BACKORDERED UNITS" badge={<AurixBadge variant="danger" pulse>STOCKOUT</AurixBadge>}>
        <div className="flex items-baseline justify-between mt-2">
          <span className="text-2xl font-bold text-[#FF6B6B]">{summary.backorderedUnitsCount} pcs</span>
          <AlertOctagon className="w-5 h-5 text-[#FF6B6B]" />
        </div>
        <div className="text-[11px] text-slate-400 mt-1">Unfulfilled demand awaiting stock intake</div>
      </AurixCard>

      <AurixCard title="IMMEDIATE ATP COVERAGE" badge={<AurixBadge variant="info">AVAILABILITY</AurixBadge>}>
        <div className="flex items-baseline justify-between mt-2">
          <span className="text-2xl font-bold text-[#D4AF37]">{summary.immediateAtpCoveragePercent}%</span>
          <ShoppingBag className="w-5 h-5 text-[#D4AF37]" />
        </div>
        <div className="text-[11px] text-slate-400 mt-1">Orders fulfillable from unallocated on-hand</div>
      </AurixCard>
    </div>
  );
};