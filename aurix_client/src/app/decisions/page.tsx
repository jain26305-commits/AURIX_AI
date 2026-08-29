'use client';

import React from 'react';
import { DomainWorkspaceOrchestrator } from '@/components/domain/DomainWorkspaceOrchestrator';
import { DecisionCard } from '@/components/visualizations/DecisionCard';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';

export default function DecisionsPage() {
  const decisions = [
    {
      id: 'DEC-8901',
      title: 'Multi-Echelon Buffer Rebalance: Tirupur Hub -> Delhi Regional DC',
      domain: 'SUPPLY CHAIN',
      expectedValue: '+$38,400',
      confidenceScore: 94,
      riskLevel: 'LOW' as const,
      preflightStatus: 'PASSED' as const,
      rationale: 'Reallocates 4,200 units from surplus factory inventory to cover projected regional demand spike with zero stockout risk.',
    },
    {
      id: 'DEC-8902',
      title: 'Expedited Air Freight Offset for Fast-Moving SKU-001',
      domain: 'LOGISTICS',
      expectedValue: '+$14,200',
      confidenceScore: 91,
      riskLevel: 'MEDIUM' as const,
      preflightStatus: 'PASSED' as const,
      rationale: 'Mitigates JNPT container hold by routing 800 priority units via domestic air corridor to protect Tier-A SLA fulfillment.',
    },
  ];

  return (
    <DomainWorkspaceOrchestrator
      domainKey="decisions"
      renderWorkspace={(subdomainId) => (
        <div className="space-y-6">
          {subdomainId === 'feed' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {decisions.map((dec) => (
                <DecisionCard key={dec.id} {...dec} />
              ))}
            </div>
          )}

          {subdomainId === 'tradeoffs' && (
            <AurixCard title="PARETO TRADEOFF FRONTIER" badge={<AurixBadge variant="gold">OPTIMIZER READY</AurixBadge>}>
              <div className="h-44 flex items-center justify-center border border-dashed border-white/10 rounded-lg font-mono text-xs text-slate-500">
                [ SERVICE LEVEL (OTIF) VS. WORKING CAPITAL HOLDING COST FRONTIER ]
              </div>
            </AurixCard>
          )}

          {subdomainId === 'preflight' && (
            <AurixCard title="PREFLIGHT SECURITY & GOVERNANCE GATE" badge={<AurixBadge variant="success">100% CLEARANCE</AurixBadge>}>
              <div className="space-y-3 font-mono text-xs pt-2">
                <div className="flex justify-between border-b border-white/5 pb-2">
                  <span className="text-slate-400">ROW-LEVEL SECURITY (RLS) CONSTRAINT:</span>
                  <span className="text-[#3DDB91] font-bold">VERIFIED</span>
                </div>
                <div className="flex justify-between border-b border-white/5 pb-2">
                  <span className="text-slate-400">FINANCIAL THRESHOLD APPROVAL:</span>
                  <span className="text-[#3DDB91] font-bold">PASSED (&lt; $50K DELEGATION)</span>
                </div>
              </div>
            </AurixCard>
          )}

          {subdomainId === 'history' && (
            <AurixCard title="ACTION EXECUTION & LEARNING AUDIT" badge={<AurixBadge variant="gold">IMMUTABLE</AurixBadge>}>
              <div className="h-40 flex items-center justify-center border border-dashed border-white/10 rounded-lg font-mono text-xs text-slate-500">
                [ REALIZED VALUE ATTRIBUTION & HISTORICAL DECISION LEDGER ]
              </div>
            </AurixCard>
          )}
        </div>
      )}
    />
  );
}
