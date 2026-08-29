'use client';

import React from 'react';
import { DomainWorkspaceOrchestrator } from '@/components/domain/DomainWorkspaceOrchestrator';
import { useManufacturing } from '@/hooks/useManufacturing';
import { OeeDecompositionView } from '@/components/visualizations/OeeDecompositionView';
import { ManufacturingStatsBar } from '@/components/features/manufacturing/ManufacturingStatsBar';
import { BomHierarchyTree } from '@/components/features/manufacturing/BomHierarchyTree';
import { MrpScheduleTable } from '@/components/features/manufacturing/MrpScheduleTable';
import { WorkCenterCapacityCard } from '@/components/features/manufacturing/WorkCenterCapacityCard';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';


function ManufacturingWorkspace({ subdomainId }: { subdomainId: string }) {
  const { data, loading, selectedSkuId, setSelectedSkuId, activeBom, activeMrpPlan } = useManufacturing();

  if (loading || !data) {
    return (
      <div className="py-24 flex flex-col items-center justify-center text-center space-y-4 font-mono">
        <div className="w-8 h-8 rounded-full border-2 border-gold border-t-transparent animate-spin" />
        <p className="text-xs text-slate-400 tracking-widest uppercase">EXPLODING BOM & WORK CENTER TELEMETRY...</p>
      </div>
    );
  }

  const bottlenecks = (data.workCenters || []).filter((wc: any) => wc.isBottleneck);
  const exceptions = data.exceptions || [];

  return (
    <div className="space-y-6">
      <ManufacturingStatsBar summary={data.summary} />

      {/* OVERVIEW / EXECUTIVE PULSE */}
      {subdomainId === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-pure-fade">
          <AurixCard title="ACTIVE WORK CENTER CONSTRAINTS" badge={<AurixBadge variant="danger">{bottlenecks.length} BOTTLENECK</AurixBadge>}>
            <div className="space-y-3 pt-2 font-mono text-xs">
              {bottlenecks.map((wc: any) => (
                <div key={wc.workCenterId} className="p-3 rounded-lg bg-[#FF6B6B]/10 border border-[#FF6B6B]/30 space-y-1">
                  <div className="flex justify-between items-center">
                    <span className="text-white font-bold">{wc.workCenterName}</span>
                    <span className="text-[#FF8585] font-bold">{wc.utilizationPercent}% LOAD</span>
                  </div>
                  <p className="text-slate-400 font-sans text-[11px]">
                    Constraint Driver: {wc.primaryConstrainingOperation} ({wc.facilityLocation})
                  </p>
                </div>
              ))}
              {bottlenecks.length === 0 && (
                <div className="h-20 flex items-center justify-center text-slate-500">NO ACTIVE BOTTLENECKS DETECTED</div>
              )}
            </div>
          </AurixCard>

          <AurixCard title="ACTIVE MRP EXCEPTIONS & SHORTAGES" badge={<AurixBadge variant="warning">{exceptions.length} ALERTS</AurixBadge>}>
            <div className="space-y-3 pt-2 font-mono text-xs">
              {exceptions.map((exc: any) => (
                <div key={exc.exceptionId} className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.06] space-y-1">
                  <div className="flex justify-between items-center">
                    <span className="text-gold font-bold">{exc.skuName}</span>
                    <AurixBadge variant={exc.severity === 'CRITICAL' ? 'danger' : 'warning'} size="sm">
                      {exc.severity}
                    </AurixBadge>
                  </div>
                  <p className="text-slate-300 font-sans text-[11px]">{exc.message}</p>
                  <p className="text-slate-500 font-sans text-[10px] pt-1">Remediation: {exc.suggestedRemediation}</p>
                </div>
              ))}
            </div>
          </AurixCard>
        </div>
      )}

      {/* SCHEDULE & MRP */}
      {subdomainId === 'schedule' && (
        <div className="space-y-6 animate-pure-fade">
          {activeMrpPlan ? (
            <MrpScheduleTable
              plan={activeMrpPlan}
              availablePlans={data.mrpPlans}
              selectedSkuId={selectedSkuId}
              onSelectSku={setSelectedSkuId}
            />
          ) : (
            <AurixCard title="PRODUCTION SCHEDULE & WIP QUEUE" badge={<AurixBadge variant="gold">NO ACTIVE PLAN</AurixBadge>}>
              <div className="h-32 flex items-center justify-center font-mono text-xs text-slate-500">
                NO MRP SCHEDULE AVAILABLE FOR CURRENT SELECTION
              </div>
            </AurixCard>
          )}
        </div>
      )}

      {/* MRP EXPLOSION */}
      {subdomainId === 'mrp' && (
        <div className="space-y-6 animate-pure-fade">
          {activeBom ? (
            <BomHierarchyTree
              bom={activeBom}
              availableBoms={data.boms}
              selectedSkuId={selectedSkuId}
              onSelectSku={setSelectedSkuId}
            />
          ) : (
            <AurixCard title="MULTI-LEVEL BOM EXPLODER" badge={<AurixBadge variant="warning">NO BOM FOUND</AurixBadge>}>
              <div className="h-32 flex items-center justify-center font-mono text-xs text-slate-500">
                NO BILL OF MATERIALS ON RECORD FOR CURRENT SELECTION
              </div>
            </AurixCard>
          )}
        </div>
      )}

      {/* CAPACITY WORK CENTERS */}
      {subdomainId === 'capacity' && (
        <div className="space-y-6 animate-pure-fade">
          <WorkCenterCapacityCard workCenters={data.workCenters} />
        </div>
      )}

      {/* OEE DECOMPOSITION */}
      {subdomainId === 'bottlenecks' && (
        <div className="space-y-6 animate-pure-fade">
          <OeeDecompositionView />
        </div>
      )}

      {/* QUALITY & SCRAP */}
      {subdomainId === 'quality' && (
        <AurixCard
          title="QUALITY & SCRAP PARETO"
          badge={<AurixBadge variant="gold">{data.summary?.scrapRatePct ?? '1.4'}% SCRAP</AurixBadge>}
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2 font-mono text-xs">
            <div className="space-y-2.5">
              {[
                { cause: 'Stitching seam misalignment', pct: 34 },
                { cause: 'Fabric shade variance (dye lot)', pct: 26 },
                { cause: 'Trim/label placement defect', pct: 18 },
                { cause: 'Print registration error', pct: 14 },
                { cause: 'Packaging damage in-line', pct: 8 },
              ].map((row) => (
                <div key={row.cause}>
                  <div className="flex justify-between mb-1">
                    <span className="text-slate-300">{row.cause}</span>
                    <span className="text-white font-bold">{row.pct}%</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-[#FF6B6B]/50 to-[#FF6B6B] rounded-full" style={{ width: `${row.pct}%` }} />
                  </div>
                </div>
              ))}
            </div>
            <p className="text-slate-400 font-sans leading-relaxed">
              Non-conformance events are logged at the work-center level and root-caused via Pareto
              analysis. Stitching seam misalignment remains the leading contributor to scrap cost this
              period, concentrated on Line 3.
            </p>
          </div>
        </AurixCard>
      )}
    </div>
  );
}

export default function ManufacturingPage() {
  return (
    <DomainWorkspaceOrchestrator
      domainKey="manufacturing"
      renderWorkspace={(subdomainId) => <ManufacturingWorkspace subdomainId={subdomainId} />}
    />
  );
}

