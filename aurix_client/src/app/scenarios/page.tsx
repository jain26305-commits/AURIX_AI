'use client';

import React from 'react';
import { DomainWorkspaceOrchestrator } from '@/components/domain/DomainWorkspaceOrchestrator';
import { DistributionCurve } from '@/components/visualizations/DistributionCurve';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';

export default function ScenariosPage() {
  const monteCarloMetric = {
    p10: 1420000,
    p50: 1230000,
    p90: 980000,
    expectedValue: 1210000,
    unit: '$',
  };

  return (
    <DomainWorkspaceOrchestrator
      domainKey="scenarios"
      renderWorkspace={(subdomainId) => (
        <div className="space-y-6">
          {subdomainId === 'simulator' && (
            <AurixCard title="WHAT-IF DIGITAL TWIN PARAMETER SHOCKS" badge={<AurixBadge variant="gold">FIDELITY: 99.2%</AurixBadge>}>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2 font-mono text-xs">
                <div className="p-3 bg-white/[0.02] rounded border border-white/5">
                  <span className="text-slate-500 text-[9px] block">LEAD TIME SHOCK</span>
                  <span className="text-white font-bold">+6 Days Delay</span>
                </div>
                <div className="p-3 bg-white/[0.02] rounded border border-white/5">
                  <span className="text-slate-500 text-[9px] block">DEMAND SPIKE</span>
                  <span className="text-white font-bold">+25% Volume</span>
                </div>
                <div className="p-3 bg-white/[0.02] rounded border border-white/5">
                  <span className="text-slate-500 text-[9px] block">RAW MATERIAL COST</span>
                  <span className="text-white font-bold">+8.4% Inflation</span>
                </div>
              </div>
            </AurixCard>
          )}

          {subdomainId === 'monte-carlo' && (
            <DistributionCurve
              title="STOCHASTIC MARGIN AT RISK (MONTE CARLO)"
              metric={monteCarloMetric}
              iterations={10000}
            />
          )}

          {subdomainId === 'counterfactuals' && (
            <AurixCard title="COUNTERFACTUAL CAUSAL ANALYSIS" badge={<AurixBadge variant="gold">CAUSAL GRAPH</AurixBadge>}>
              <div className="h-40 flex items-center justify-center border border-dashed border-white/10 rounded-lg font-mono text-xs text-slate-500">
                [ CAUSAL ATTRIBUTION ISOLATING POLICY INTERVENTIONS FROM MACRO NOISE ]
              </div>
            </AurixCard>
          )}

          {subdomainId === 'comparison' && (
            <AurixCard title="SCENARIO COMPARISON BRIDGE" badge={<AurixBadge variant="success">+$84K VARIANCE</AurixBadge>}>
              <div className="h-40 flex items-center justify-center border border-dashed border-white/10 rounded-lg font-mono text-xs text-slate-500">
                [ SIDE-BY-SIDE DELTA DELIBERATION: PROPOSED TWIN VS. BASELINE ]
              </div>
            </AurixCard>
          )}
        </div>
      )}
    />
  );
}
