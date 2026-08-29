'use client';

import React from 'react';
import Link from 'next/link';
import { DomainWorkspaceOrchestrator } from '@/components/domain/DomainWorkspaceOrchestrator';
import { useRiskAssurance } from '@/hooks/useRiskAssurance';
import { RiskRadarView } from '@/components/visualizations/RiskRadarView';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { AlertTriangle, CheckCircle2, Network, Bell, FolderKanban, ArrowRight } from 'lucide-react';

const severityVariant: Record<string, 'success' | 'gold' | 'warning' | 'danger'> = {
  LOW: 'success',
  MEDIUM: 'gold',
  HIGH: 'warning',
  CRITICAL: 'danger',
};

function OperationalLinkBar() {
  return (
    <div className="flex flex-col sm:flex-row gap-3">
      <Link
        href="/risk-assurance/alerts"
        className="flex-1 flex items-center justify-between gap-3 p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.06] hover:border-gold/40 hover:bg-gold/5 transition-all group"
      >
        <span className="flex items-center gap-2.5 text-xs font-mono text-slate-300">
          <Bell className="w-4 h-4 text-gold" />
          Operational Alerts & Triage Center
        </span>
        <ArrowRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-gold group-hover:translate-x-0.5 transition-all" />
      </Link>
      <Link
        href="/risk-assurance/cases"
        className="flex-1 flex items-center justify-between gap-3 p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.06] hover:border-gold/40 hover:bg-gold/5 transition-all group"
      >
        <span className="flex items-center gap-2.5 text-xs font-mono text-slate-300">
          <FolderKanban className="w-4 h-4 text-gold" />
          Operational Case Management
        </span>
        <ArrowRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-gold group-hover:translate-x-0.5 transition-all" />
      </Link>
    </div>
  );
}

function RiskAssuranceWorkspace({ subdomainId }: { subdomainId: string }) {
  const { riskSummary, priorities, findings, loading } = useRiskAssurance();

  if (loading || !riskSummary) {
    return (
      <div className="py-24 flex flex-col items-center justify-center text-center space-y-4 font-mono">
        <div className="w-8 h-8 rounded-full border-2 border-gold border-t-transparent animate-spin" />
        <p className="text-xs text-slate-400 tracking-widest uppercase">RUNNING ASSURANCE AUDIT & RISK PROPAGATION...</p>
      </div>
    );
  }

  let content: React.ReactNode = null;

  if (subdomainId === 'vulnerability' || subdomainId === 'assurance') {
    content = <RiskRadarView />;
  } else if (subdomainId === 'leakage') {
    const totalExposure = findings.reduce((sum, f) => sum + f.financial_exposure, 0);
    content = (
      <AurixCard
        title="FINANCIAL LEAKAGE MITIGATION"
        badge={<AurixBadge variant="danger">${(totalExposure / 1000).toFixed(1)}K IDENTIFIED</AurixBadge>}
      >
        <div className="space-y-3 pt-2 font-mono text-xs">
          {findings.map((f) => (
            <div key={f.finding_id} className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06]">
              <div className="flex items-center justify-between mb-2">
                <span className="text-white font-bold flex items-center gap-1.5">
                  {f.status === 'REMEDIATED' ? (
                    <CheckCircle2 className="w-3.5 h-3.5 text-[#3DDB91]" />
                  ) : (
                    <AlertTriangle className="w-3.5 h-3.5 text-[#F3B33D]" />
                  )}
                  {f.title}
                </span>
                <div className="flex items-center gap-2">
                  <AurixBadge variant={f.status === 'REMEDIATED' ? 'success' : severityVariant[f.severity]} size="sm">
                    {f.status === 'REMEDIATED' ? 'REMEDIATED' : f.severity}
                  </AurixBadge>
                </div>
              </div>
              <p className="text-slate-400 font-sans leading-relaxed mb-2">{f.description}</p>
              <div className="flex items-center justify-between text-[10px] pt-2 border-t border-white/[0.05]">
                <span className="text-slate-500">{f.domain.replace(/_/g, ' ')}</span>
                <span className="text-gold font-bold">${f.financial_exposure.toLocaleString()} EXPOSURE</span>
              </div>
              {f.recommended_action && (
                <div className="mt-2 text-[10px] text-slate-500 italic">→ {f.recommended_action}</div>
              )}
            </div>
          ))}
        </div>
      </AurixCard>
    );
  } else if (subdomainId === 'disruptions') {
    content = (
      <AurixCard
        title="DISRUPTION PROPAGATION CASCADE"
        badge={<AurixBadge variant="warning">{riskSummary.criticalRisksCount ?? priorities.filter((p) => p.severity === 'CRITICAL').length} CRITICAL</AurixBadge>}
      >
        <div className="space-y-3 pt-2 font-mono text-xs">
          {priorities.map((risk) => (
            <div key={risk.riskId} className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06]">
              <div className="flex items-center justify-between mb-2">
                <span className="text-white font-bold flex items-center gap-1.5">
                  <Network className="w-3.5 h-3.5 text-[#FF6B6B]" />
                  {risk.title}
                </span>
                <AurixBadge variant={severityVariant[risk.severity || 'MEDIUM']} size="sm">{risk.severity}</AurixBadge>
              </div>
              <p className="text-slate-400 font-sans leading-relaxed mb-2">{risk.description}</p>
              <div className="grid grid-cols-3 gap-3 text-[10px] pt-2 border-t border-white/[0.05]">
                <div><span className="text-slate-500 block">PROBABILITY</span><span className="text-white font-bold">{((risk.probability || 0) * 100).toFixed(0)}%</span></div>
                <div><span className="text-slate-500 block">IMPACT</span><span className="text-white font-bold">${(risk.impactAmountUsd || 0).toLocaleString()}</span></div>
                <div><span className="text-slate-500 block">EXPOSURE</span><span className="text-gold font-bold">${(risk.exposureAmountUsd || 0).toLocaleString()}</span></div>
              </div>
            </div>
          ))}
        </div>
      </AurixCard>
    );
  }

  if (!content) return null;

  return (
    <div className="space-y-6">
      <OperationalLinkBar />
      {content}
    </div>
  );
}

export default function RiskAssurancePage() {
  return (
    <DomainWorkspaceOrchestrator
      domainKey="risk-assurance"
      renderWorkspace={(subdomainId) => <RiskAssuranceWorkspace subdomainId={subdomainId} />}
    />
  );
}

