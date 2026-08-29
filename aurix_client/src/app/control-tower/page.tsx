'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { FinancialImpactExposureCard } from '@/components/features/control-tower/FinancialImpactExposureCard';
import { ControlTowerHealthGrid } from '@/components/features/control-tower/ControlTowerHealthGrid';
import { TopSignalsActionFeed } from '@/components/features/control-tower/TopSignalsActionFeed';
import { useControlTower } from '@/hooks/useControlTower';
import { IntakeService, CapabilityReadinessReport } from '@/services/api/intakeService';
import { AurixButton } from '@/components/ui/AurixButton';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { ArrowRight, RotateCw, Layers } from 'lucide-react';
import { useWorkspaceHeader } from '@/context/WorkspaceHeaderContext';

export default function ControlTowerPage() {
  useWorkspaceHeader({ activeWorkspaceTitle: "Enterprise Control Tower" });
  const router = useRouter();
  const { data, loading, reload } = useControlTower();
  const [readiness, setReadiness] = useState<CapabilityReadinessReport | null>(null);

  useEffect(() => {
    IntakeService.getCapabilityReadiness()
      .then(setReadiness)
      .catch(() => null);
  }, []);

  if (loading || !data) {
    return (
      <>
        <div className="py-24 flex flex-col items-center justify-center text-center space-y-4 font-mono">
          <div className="w-8 h-8 rounded-full border-2 border-gold border-t-transparent animate-spin" />
          <p className="text-xs text-slate-400 tracking-widest uppercase">
            CALCULATING ENTERPRISE CONTROL TOWER SNAPSHOT...
          </p>
        </div>
      </>
    );
  }

  const partialModules = readiness?.modules?.filter((m) => m.status === 'PARTIAL') ?? [];

  return (
    <>
      <div className="space-y-8 animate-pure-fade font-mono">
        {/* Workspace Top Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2 py-0.5 rounded bg-gold/10 border border-gold/30 text-gold text-[10px] font-bold tracking-widest uppercase">
                EXECUTIVE DECISION CENTER
              </span>
              <span className="text-slate-500 text-xs">â€¢ TENANT: {data.tenantId}</span>
            </div>
            <h1 className="text-xl font-bold text-white tracking-wide">ENTERPRISE COMMAND & CONTROL TOWER</h1>
            <p className="text-xs text-slate-400 mt-0.5">
              Autonomous cross-functional visibility, signal attribution, and financial exposure mitigation.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <AurixButton variant="secondary" size="sm" onClick={reload}>
              <RotateCw className="w-3.5 h-3.5 mr-1.5" /> RE-AUDIT
            </AurixButton>
            <AurixButton variant="gold" size="sm" onClick={() => router.push('/decisions/recommendations')}>
              <span>ADVISOR & ACTIONS</span>
              <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
            </AurixButton>
          </div>
        </div>

        {/* Dynamic Capability Readiness Ribbon */}
        {readiness && (
          <div className="p-3.5 rounded-xl bg-[#0C0E12] border border-white/[0.08] flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-gold/10 border border-gold/30 text-gold shrink-0">
                <Layers className="w-4 h-4" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-white font-bold">AURIX CAPABILITY GATES:</span>
                  <span className="text-gold font-bold">{readiness.overallPlatformReadinessPercent}% ACTIVE</span>
                  <AurixBadge variant={partialModules.length === 0 ? 'success' : 'warning'}>
                    {partialModules.length === 0 ? 'ALL CAPABILITIES UNLOCKED' : `${partialModules.length} MODULE PENDING CALIBRATION`}
                  </AurixBadge>
                </div>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  {partialModules.length > 0
                    ? `Manufacturing & MRP requires shift capacity inputs before autonomous scheduling.`
                    : `Full multi-echelon demand, inventory, logistics, and capital models active.`}
                </p>
              </div>
            </div>

            <button
              onClick={() => router.push('/data/intake')}
              className="px-3 py-1.5 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] text-gold font-bold transition-all text-[11px] flex items-center justify-center gap-1.5 cursor-pointer shrink-0 border border-white/10"
            >
              <span>MANAGE INGESTION & CONNECTORS</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>
        )}

        {/* 1. Executive Financial Snapshot Bar */}
        <FinancialImpactExposureCard financials={data.financials} />

        {/* 2. Top Prescriptive Action Feed */}
        <TopSignalsActionFeed signals={data.urgentSignals} />

        {/* 3. 8-Pillar Strategic Health Radar Grid */}
        <ControlTowerHealthGrid pillars={data.pillars} />
      </div>
    </>
  );
}
