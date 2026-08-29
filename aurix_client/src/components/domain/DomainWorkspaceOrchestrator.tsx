'use client';

import React, { Suspense } from 'react';
import { DomainLandingView } from '@/components/domain/DomainLandingView';
import { PageHeader } from '@/components/ui/PageHeader';
import { useDomainNavigation } from '@/hooks/useDomainNavigation';
import { useWorkspaceHeader } from '@/context/WorkspaceHeaderContext';
import { DOMAIN_REGISTRY } from '@/config/domainRegistry';

export interface DomainWorkspaceOrchestratorProps {
  domainKey: string;
  renderWorkspace?: (activeSubdomainId: string, onBack: () => void) => React.ReactNode;
  children?: React.ReactNode;
}

function DomainWorkspaceInner({
  domainKey,
  renderWorkspace,
  children,
}: DomainWorkspaceOrchestratorProps) {
  const { domain, activeSubdomainId, activeSubdomain, selectSubdomain, isLanding } =
    useDomainNavigation(domainKey);

  const activeDef = domain || DOMAIN_REGISTRY[domainKey];

  useWorkspaceHeader({
    domainTitle: activeDef?.title ?? 'WORKSPACE',
    subdomainTitle: activeSubdomain?.title,
  });

  if (!activeDef) {
    return (
      <div className="p-8 text-center font-mono text-xs text-slate-500">
        DOMAIN DEFINITION NOT FOUND: {domainKey}
      </div>
    );
  }

  return (
    <>
      {isLanding ? (
        <DomainLandingView
          domainTag={activeDef.domainTag}
          title={activeDef.title}
          description={activeDef.description}
          kpis={activeDef.kpis}
          signals={activeDef.signals}
          subdomains={activeDef.subdomains}
          activeSubdomainId={activeSubdomainId}
          onSelectSubdomain={(id) => selectSubdomain(id)}
          status={activeDef.status}
          telemetryStream={activeDef.telemetryStream}
        />
      ) : (
        <div className="space-y-6 animate-slide-up">
          <PageHeader
            title={activeSubdomain?.title || 'WORKSPACE'}
            subtitle={activeSubdomain?.description}
            onBack={() => selectSubdomain(null)}
          />
          {renderWorkspace
            ? renderWorkspace(activeSubdomainId || '', () => selectSubdomain(null))
            : children}
        </div>
      )}
    </>
  );
}

export const DomainWorkspaceOrchestrator: React.FC<DomainWorkspaceOrchestratorProps> = (
  props
) => {
  return (
    <Suspense
      fallback={
        <div className="min-h-[60vh] flex items-center justify-center font-mono text-xs text-[#D4AF37] tracking-widest uppercase">
          INITIALIZING {props.domainKey.toUpperCase()} WORKSPACE...
        </div>
      }
    >
      <DomainWorkspaceInner {...props} />
    </Suspense>
  );
};
