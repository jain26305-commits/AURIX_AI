'use client';

import React from 'react';
import { DomainLandingHero, DomainKpi } from './DomainLandingHero';
import { DomainSignalsOverview, DomainSignal } from './DomainSignalsOverview';
import { SubdomainWorkspaceSelector, SubdomainItem } from '../navigation/SubdomainWorkspaceSelector';

export interface DomainLandingViewProps {
  domainTag: string;
  title: string;
  description: string;
  kpis?: DomainKpi[];
  signals?: DomainSignal[];
  subdomains: SubdomainItem[];
  activeSubdomainId?: string | null;
  onSelectSubdomain: (id: string) => void;
  status?: 'OPTIMAL' | 'DEGRADED' | 'WATCH' | 'CRITICAL';
  telemetryStream?: string;
}

export const DomainLandingView: React.FC<DomainLandingViewProps> = ({
  domainTag,
  title,
  description,
  kpis = [],
  signals = [],
  subdomains,
  activeSubdomainId,
  onSelectSubdomain,
  status,
  telemetryStream,
}) => {
  return (
    <div className="space-y-8 animate-pure-fade">
      <DomainLandingHero
        domainTag={domainTag}
        title={title}
        description={description}
        kpis={kpis}
        status={status}
        telemetryStream={telemetryStream}
      />
      {signals.length > 0 && <DomainSignalsOverview signals={signals} />}
      <SubdomainWorkspaceSelector
        subdomains={subdomains}
        activeSubdomainId={activeSubdomainId}
        onSelectSubdomain={onSelectSubdomain}
      />
    </div>
  );
};
