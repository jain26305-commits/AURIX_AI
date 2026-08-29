'use client';

import React from 'react';
import { DomainWorkspaceOrchestrator } from '@/components/domain/DomainWorkspaceOrchestrator';
import { AgentExecutionStream } from '@/components/visualizations/AgentExecutionStream';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';

export default function AgentStudioPage() {
  return (
    <DomainWorkspaceOrchestrator
      domainKey="agents"
      renderWorkspace={(subdomainId) => (
        <div className="space-y-6">
          {(subdomainId === 'fleet' || subdomainId === 'execution') && <AgentExecutionStream />}
          {subdomainId === 'governance' && (
            <AurixCard title="AI GUARDRAILS & CIRCUIT BREAKERS" badge={<AurixBadge variant="success">100% ENFORCED</AurixBadge>}>
              <div className="h-44 flex items-center justify-center border border-dashed border-white/10 rounded-lg font-mono text-xs text-slate-500">
                [ TOKEN BUDGET POLICIES, RATE LIMITS & HUMAN-IN-THE-LOOP APPROVAL GATES ]
              </div>
            </AurixCard>
          )}
          {subdomainId === 'studio' && (
            <AurixCard title="MULTI-AGENT DAG STUDIO" badge={<AurixBadge variant="gold">PHASE 30 STUDIO</AurixBadge>}>
              <div className="h-44 flex items-center justify-center border border-dashed border-white/10 rounded-lg font-mono text-xs text-slate-500">
                [ VISUAL MULTI-AGENT DAG WORKFLOW DESIGNER & DEPLOYMENT PIPELINE ]
              </div>
            </AurixCard>
          )}
        </div>
      )}
    />
  );
}
