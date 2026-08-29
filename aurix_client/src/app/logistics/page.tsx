'use client';

import React from 'react';
import { DomainWorkspaceOrchestrator } from '@/components/domain/DomainWorkspaceOrchestrator';
import { useLogisticsIntelligence } from '@/hooks/useLogisticsIntelligence';
import { ShipmentTransitTracker } from '@/components/features/logistics/ShipmentTransitTracker';
import { LaneRiskOverview } from '@/components/features/logistics/LaneRiskOverview';
import { NodeDelayHeatmap } from '@/components/features/logistics/NodeDelayHeatmap';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { Truck, PieChart, Landmark } from 'lucide-react';

function LogisticsWorkspace({ subdomainId }: { subdomainId: string }) {
  const { data, loading } = useLogisticsIntelligence();

  if (loading || !data) {
    return (
      <div className="py-24 flex flex-col items-center justify-center text-center space-y-4 font-mono">
        <div className="w-8 h-8 rounded-full border-2 border-gold border-t-transparent animate-spin" />
        <p className="text-xs text-slate-400 tracking-widest uppercase">SYNCING TMS & TELEMATICS FEED...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <AurixCard title="ACTIVE SHIPMENTS" badge={<AurixBadge variant="gold">IN-FLIGHT</AurixBadge>}>
          <div className="flex items-baseline justify-between mt-2">
            <span className="text-2xl font-bold text-white">{data.summary.totalActiveShipments}</span>
            <Truck className="w-5 h-5 text-gold" />
          </div>
          <div className="text-[11px] text-slate-400 mt-1">{data.summary.totalInTransitUnits.toLocaleString()} units in transit</div>
        </AurixCard>
        <AurixCard title="PORTFOLIO ON-TIME RATE" badge={<AurixBadge variant="success">RELIABILITY</AurixBadge>}>
          <div className="flex items-baseline justify-between mt-2">
            <span className="text-2xl font-bold text-[#3DDB91]">{data.summary.portfolioOnTimeTransitPercent}%</span>
            <PieChart className="w-5 h-5 text-[#3DDB91]" />
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Across all monitored lanes</div>
        </AurixCard>
        <AurixCard title="CAPITAL IN TRANSIT" badge={<AurixBadge variant="gold">EXPOSURE</AurixBadge>}>
          <div className="flex items-baseline justify-between mt-2">
            <span className="text-2xl font-bold text-white">₹{(data.summary.totalInTransitValuationINR / 100000).toFixed(1)}L</span>
            <Landmark className="w-5 h-5 text-gold" />
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Valuation of goods currently moving</div>
        </AurixCard>
        <AurixCard title="DELAY RISK SHIPMENTS" badge={<AurixBadge variant="danger" pulse>ATTENTION</AurixBadge>}>
          <div className="flex items-baseline justify-between mt-2">
            <span className="text-2xl font-bold text-[#FF6B6B]">{data.summary.shipmentsAtDelayRiskCount}</span>
            <Truck className="w-5 h-5 text-[#FF6B6B]" />
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Exceeding P90 transit benchmark</div>
        </AurixCard>
      </div>

      {subdomainId === 'shipments' && <ShipmentTransitTracker shipments={data.shipments} />}

      {subdomainId === 'carriers' && (
        <AurixCard title="CARRIER RATE COMPLIANCE & DAMAGE CLAIMS" badge={<AurixBadge variant="gold">SCORECARD</AurixBadge>}>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2 font-mono text-xs">
            {Array.from(new Set(data.shipments.map((s) => s.carrierName))).slice(0, 6).map((carrier) => {
              const carrierShipments = data.shipments.filter((s) => s.carrierName === carrier);
              const onTime = carrierShipments.filter((s) => s.status !== 'DELAYED').length;
              const rate = carrierShipments.length > 0 ? Math.round((onTime / carrierShipments.length) * 100) : 0;
              return (
                <div key={carrier} className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.05]">
                  <div className="text-white font-bold truncate">{carrier}</div>
                  <div className="flex items-center justify-between mt-2">
                    <span className="text-slate-500">ACTIVE LOADS</span>
                    <span className="text-white">{carrierShipments.length}</span>
                  </div>
                  <div className="flex items-center justify-between mt-1">
                    <span className="text-slate-500">ON-TIME RATE</span>
                    <span className={rate >= 90 ? 'text-[#3DDB91] font-bold' : 'text-[#F3B33D] font-bold'}>{rate}%</span>
                  </div>
                </div>
              );
            })}
          </div>
        </AurixCard>
      )}

      {subdomainId === 'lanes' && (
        <div className="space-y-6">
          <LaneRiskOverview lanes={data.lanes} />
          <NodeDelayHeatmap lanes={data.lanes} />
        </div>
      )}

      {subdomainId === 'freight' && (
        <AurixCard title="FREIGHT COST ECONOMICS & FUEL SURCHARGE AUDIT" badge={<AurixBadge variant="success">AUDITED</AurixBadge>}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2 font-mono text-xs">
            <div className="space-y-2.5">
              {data.lanes.slice(0, 5).map((lane) => (
                <div key={lane.laneId} className="flex justify-between border-b border-white/5 pb-2">
                  <span className="text-slate-300">{lane.origin} → {lane.destination}</span>
                  <span className="text-white font-bold">₹{(lane.totalCapitalInTransitINR / lane.totalUnitsInTransit || 0).toFixed(0)}/unit</span>
                </div>
              ))}
            </div>
            <p className="text-slate-400 font-sans leading-relaxed">
              Freight invoice auditing reconciles carrier-billed fuel surcharges against published lane
              indices, flagging over-billed shipments for dispute and recovery.
            </p>
          </div>
        </AurixCard>
      )}
    </div>
  );
}

export default function LogisticsPage() {
  return (
    <DomainWorkspaceOrchestrator
      domainKey="logistics"
      renderWorkspace={(subdomainId) => <LogisticsWorkspace subdomainId={subdomainId} />}
    />
  );
}
