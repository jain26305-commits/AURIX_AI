'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { AurixWaterfallChart } from '@/components/charts/AurixWaterfallChart';
import { useFinanceIntelligence } from '@/hooks/useFinanceIntelligence';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { AurixButton } from '@/components/ui/AurixButton';
import { ArrowRight, RotateCw } from 'lucide-react';
import { useWorkspaceHeader } from '@/context/WorkspaceHeaderContext';

export default function FinancePage() {
  useWorkspaceHeader({ activeWorkspaceTitle: "Financial Decisions" });
  const router = useRouter();
  const { data, loading, reload } = useFinanceIntelligence();

  if (loading || !data) {
    return (
      <>
        <div className="py-24 flex flex-col items-center justify-center text-center space-y-4">
          <div className="w-8 h-8 rounded-full border-2 border-gold border-t-transparent animate-spin" />
          <p className="text-xs font-mono text-slate-400 tracking-widest uppercase">
            CALCULATING WORKING CAPITAL EXPOSURE & LIQUIDITY BRIDGES...
          </p>
        </div>
      </>
    );
  }

  const { metrics, waterfallBridge, holdingRateAnnualPercent } = data;

  return (
    <>
      <div className="space-y-8 animate-pure-fade">
        {/* Workspace Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-white tracking-wide">WORKING CAPITAL & FINANCIAL EXPOSURE</h1>
            <p className="text-xs font-mono text-slate-400 mt-1">
              Translating supply chain decisions into balance sheet valuation, holding drag, and cash release.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <AurixButton variant="secondary" size="sm" onClick={reload}>
              <RotateCw className="w-3.5 h-3.5 mr-1.5" /> RE-AUDIT
            </AurixButton>
            <AurixButton variant="gold" size="sm" onClick={() => router.push('/decisions/scenarios')}>
              <span>SCENARIO STUDIO</span>
              <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
            </AurixButton>
          </div>
        </div>

        {/* Top Financial KPI Ribbon */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <AurixCard title="GROSS HOLDING CAPITAL" badge={<AurixBadge variant="gold">VALUATION</AurixBadge>}>
            <div className="text-2xl font-bold font-mono text-white mt-2">
              ₹{(metrics.grossInventoryValuationINR / 100000).toFixed(2)}L
            </div>
            <div className="text-[11px] font-mono text-slate-400 mt-1">
              Annual Carrying Cost ({holdingRateAnnualPercent}%): ₹{(metrics.annualHoldingCostINR / 100000).toFixed(2)}L
            </div>
          </AurixCard>

          <AurixCard title="UNLOCKED CASH OPPORTUNITY" badge={<AurixBadge variant="success">RELEASE</AurixBadge>}>
            <div className="text-2xl font-bold font-mono text-[#3DDB91] mt-2">
              ₹{(metrics.unlockedCapitalOpportunityINR / 100000).toFixed(2)}L
            </div>
            <div className="text-[11px] font-mono text-slate-400 mt-1">Recoverable via inventory rightsizing</div>
          </AurixCard>

          <AurixCard title="EXCESS DEAD CAPITAL" badge={<AurixBadge variant="warning">SLOW-MOVING</AurixBadge>}>
            <div className="text-2xl font-bold font-mono text-[#F3B33D] mt-2">
              ₹{(metrics.excessDeadStockINR / 100000).toFixed(2)}L
            </div>
            <div className="text-[11px] font-mono text-slate-400 mt-1">Tied up in variants &gt; 180 days cover</div>
          </AurixCard>

          <AurixCard title="STOCKOUT REVENUE EXPOSURE" badge={<AurixBadge variant="danger" pulse>LOSS RISK</AurixBadge>}>
            <div className="text-2xl font-bold font-mono text-[#FF6B6B] mt-2">
              ₹{(metrics.stockoutRevenueLostINR / 100000).toFixed(2)}L
            </div>
            <div className="text-[11px] font-mono text-slate-400 mt-1">Unmet demand across 3 breaching SKUs</div>
          </AurixCard>
        </div>

        {/* 1. Working Capital Waterfall Bridge */}
        <AurixWaterfallChart items={waterfallBridge} height={260} />
      </div>
    </>
  );
}