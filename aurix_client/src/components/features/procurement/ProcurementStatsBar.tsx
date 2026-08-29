'use client';

import React from 'react';
import { ProcurementSummary } from '@/types/procurement.types';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { ShoppingBag, Truck, FileCheck, AlertTriangle } from 'lucide-react';
import { formatINR } from '@/lib/formatters';

export const ProcurementStatsBar: React.FC<{ summary: ProcurementSummary }> = ({ summary }) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 select-none font-mono">
      <AurixCard title="OPEN PURCHASE ORDERS" badge={<AurixBadge variant="gold">ACTIVE BOOK</AurixBadge>}>
        <div className="flex items-baseline justify-between mt-2">
          <span className="text-2xl font-bold text-white">0{summary.totalOpenOrdersCount}</span>
          <ShoppingBag className="w-5 h-5 text-gold" />
        </div>
        <div className="text-[11px] text-slate-400 mt-1">Across 3 approved supplier mills</div>
      </AurixCard>

      <AurixCard title="INBOUND IN-TRANSIT VALUE" badge={<AurixBadge variant="info">PIPELINE</AurixBadge>}>
        <div className="flex items-baseline justify-between mt-2">
          <span className="text-2xl font-bold text-[#D4AF37]">{formatINR(summary.activeInboundValueINR)}</span>
          <Truck className="w-5 h-5 text-[#D4AF37]" />
        </div>
        <div className="text-[11px] text-slate-400 mt-1">{summary.pendingAsnCount} shipments with active ASNs</div>
      </AurixCard>

      <AurixCard title="3-WAY MATCH CLEARANCE" badge={<AurixBadge variant="success">RECONCILIATION</AurixBadge>}>
        <div className="flex items-baseline justify-between mt-2">
          <span className="text-2xl font-bold text-[#3DDB91]">{summary.threeWayMatchPassRatePercent}%</span>
          <FileCheck className="w-5 h-5 text-[#3DDB91]" />
        </div>
        <div className="text-[11px] text-slate-400 mt-1">PO vs. GRN vs. Invoice audit rate</div>
      </AurixCard>

      <AurixCard title="CRITICAL DELAYS" badge={<AurixBadge variant="danger" pulse>DELAY RISK</AurixBadge>}>
        <div className="flex items-baseline justify-between mt-2">
          <span className="text-2xl font-bold text-[#FF6B6B]">0{summary.criticalDelayedOrdersCount}</span>
          <AlertTriangle className="w-5 h-5 text-[#FF6B6B]" />
        </div>
        <div className="text-[11px] text-slate-400 mt-1">Orders exceeding promised ETA</div>
      </AurixCard>
    </div>
  );
};