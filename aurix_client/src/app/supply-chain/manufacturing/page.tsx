'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { ManufacturingStatsBar } from '@/components/features/manufacturing/ManufacturingStatsBar';
import { BomHierarchyTree } from '@/components/features/manufacturing/BomHierarchyTree';
import { MrpScheduleTable } from '@/components/features/manufacturing/MrpScheduleTable';
import { WorkCenterCapacityCard } from '@/components/features/manufacturing/WorkCenterCapacityCard';
import { useManufacturing } from '@/hooks/useManufacturing';
import { AurixButton } from '@/components/ui/AurixButton';

import { AurixBadge } from '@/components/ui/AurixBadge';
import { RotateCw, ArrowRight, Layers, Calendar, Factory, AlertTriangle } from 'lucide-react';
import { useWorkspaceHeader } from '@/context/WorkspaceHeaderContext';

export default function ManufacturingPage() {
  useWorkspaceHeader({ activeWorkspaceTitle: "Manufacturing & Planning" });
  const router = useRouter();
  const {
    data,
    loading,
    activeTab,
    setActiveTab,
    selectedSkuId,
    setSelectedSkuId,
    activeBom,
    activeMrpPlan,
    reload,
  } = useManufacturing();

  if (loading || !data || !activeBom || !activeMrpPlan) {
    return (
      <>
        <div className="py-24 flex flex-col items-center justify-center text-center space-y-4 font-mono">
          <div className="w-8 h-8 rounded-full border-2 border-gold border-t-transparent animate-spin" />
          <p className="text-xs text-slate-400 tracking-widest uppercase">
            CALCULATING MULTI-LEVEL BOM HIERARCHIES & MRP GROSS-TO-NET...
          </p>
        </div>
      </>
    );
  }

  return (
    <>
      <div className="space-y-8 animate-pure-fade font-mono">
        {/* Workspace Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2 py-0.5 rounded bg-gold/10 border border-gold/30 text-gold text-[10px] font-bold tracking-widest uppercase">
                PRODUCTION PLANNING
              </span>
              <span className="text-slate-500 text-xs">• MRP RUN & CAPACITIES</span>
            </div>
            <h1 className="text-xl font-bold text-white tracking-wide">MANUFACTURING, BOM & PLANNING CENTER</h1>
            <p className="text-xs text-slate-400 mt-0.5">
              Engineering Bill of Materials (BOM), Material Requirements Planning (MRP), and work-center capacity constraints.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <AurixButton variant="secondary" size="sm" onClick={reload}>
              <RotateCw className="w-3.5 h-3.5 mr-1.5" /> RE-SIMULATE
            </AurixButton>
            <AurixButton variant="gold" size="sm" onClick={() => router.push('/supply-chain/procurement')}>
              <span>PROCUREMENT BOOK</span>
              <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
            </AurixButton>
          </div>
        </div>

        {/* 1. Macro Summary Metric Bar */}
        <ManufacturingStatsBar summary={data?.summary || {}} />

        {/* 2. Sub-Domain Tab Navigation */}
        <div className="flex items-center gap-2 p-1.5 bg-[#0C0E12] border border-white/[0.08] rounded-xl text-xs select-none">
          <button
            onClick={() => setActiveTab('BOM_EXPLORER')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold transition-all cursor-pointer ${
              activeTab === 'BOM_EXPLORER'
                ? 'bg-white/[0.08] text-white border border-white/20'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Layers className={`w-3.5 h-3.5 ${activeTab === 'BOM_EXPLORER' ? 'text-gold' : 'text-slate-500'}`} />
            <span>BOM EXPLORER ({(data?.boms || []).length} SCHEMAS)</span>
          </button>

          <button
            onClick={() => setActiveTab('MRP_SCHEDULE')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold transition-all cursor-pointer ${
              activeTab === 'MRP_SCHEDULE'
                ? 'bg-white/[0.08] text-white border border-white/20'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Calendar className={`w-3.5 h-3.5 ${activeTab === 'MRP_SCHEDULE' ? 'text-gold' : 'text-slate-500'}`} />
            <span>MRP SCHEDULE ({(data?.mrpPlans || []).length} PLANS)</span>
          </button>

          <button
            onClick={() => setActiveTab('WORK_CENTERS')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold transition-all cursor-pointer ${
              activeTab === 'WORK_CENTERS'
                ? 'bg-white/[0.08] text-white border border-white/20'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Factory className={`w-3.5 h-3.5 ${activeTab === 'WORK_CENTERS' ? 'text-gold' : 'text-slate-500'}`} />
            <span>WORK CENTERS ({(data?.workCenters || []).length})</span>
          </button>

          <button
            onClick={() => setActiveTab('EXCEPTIONS')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold transition-all cursor-pointer ${
              activeTab === 'EXCEPTIONS'
                ? 'bg-white/[0.08] text-white border border-white/20'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <AlertTriangle className={`w-3.5 h-3.5 ${activeTab === 'EXCEPTIONS' ? 'text-gold' : 'text-slate-500'}`} />
            <span>PLANNING EXCEPTIONS ({data.exceptions.length})</span>
          </button>
        </div>

        {/* 3. Tab Views */}
        {activeTab === 'BOM_EXPLORER' && (
          <BomHierarchyTree
            bom={activeBom}
            availableBoms={data?.boms || []}
            selectedSkuId={selectedSkuId}
            onSelectSku={setSelectedSkuId}
          />
        )}

        {activeTab === 'MRP_SCHEDULE' && (
          <MrpScheduleTable
            plan={activeMrpPlan}
            availablePlans={data?.mrpPlans || []}
            selectedSkuId={selectedSkuId}
            onSelectSku={setSelectedSkuId}
          />
        )}

        {activeTab === 'WORK_CENTERS' && (
          <WorkCenterCapacityCard workCenters={data?.workCenters || []} />
        )}

        {activeTab === 'EXCEPTIONS' && (
          <div className="space-y-3">
            {data.exceptions.map((exc: any) => (
              <div
                key={exc.exceptionId}
                className="p-4 rounded-xl aurix-card-glass border border-[#FF6B6B]/30 bg-[#FF6B6B]/[0.02] flex items-start justify-between gap-4 text-xs"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <AurixBadge variant="danger">{exc.severity}</AurixBadge>
                    <span className="text-white font-bold">{exc.skuName} ({exc.skuId})</span>
                    <span className="text-slate-500 text-[10px]">• Period: {exc.period}</span>
                  </div>
                  <p className="text-slate-300 text-xs leading-relaxed">{exc.message}</p>
                  <p className="text-gold text-[11px] font-bold mt-1">➔ SUGGESTION: {exc.suggestedRemediation}</p>
                </div>
                <span className="text-slate-500 text-[10px] shrink-0">{exc.exceptionId}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}