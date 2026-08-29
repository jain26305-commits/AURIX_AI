'use client';

import React from 'react';
import { DomainWorkspaceOrchestrator } from '@/components/domain/DomainWorkspaceOrchestrator';
import { DataLineageExplorer } from '@/components/visualizations/DataLineageExplorer';
import { ReconciliationMatrix } from '@/components/features/data-integrations/ReconciliationMatrix';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { AurixButton } from '@/components/ui/AurixButton';
import Link from 'next/link';
import { DOMAIN_REGISTRY } from '@/config/domainRegistry';

function DataIntegrationsWorkspace({ subdomainId }: { subdomainId: string }) {
  if (subdomainId === 'connectors') {
    return <DataLineageExplorer />;
  }

  if (subdomainId === 'lineage') {
    return (
      <AurixCard title="LINEAGE & SOURCE AUTHORITY GRAPH" badge={<AurixBadge variant="gold">PHASE 19</AurixBadge>}>
        <div className="space-y-4 pt-2 font-mono text-xs">
          <p className="text-slate-400 font-sans leading-relaxed">
            Every canonical field is stamped with source authority, transform lineage, and a cryptographic
            checksum at ingestion time. When two sources disagree, the authority ranking below determines
            which value wins.
          </p>
          <div className="space-y-2">
            {[
              { field: 'skuId / Product Master', authority: 'SAP S/4HANA', rank: 1 },
              { field: 'On-Hand Inventory', authority: 'WMS Manhattan', rank: 1 },
              { field: 'AP / AR Ledger Entries', authority: 'Tally Prime', rank: 1 },
              { field: 'Shipment Status & ETA', authority: 'Carrier EDI & Telematics', rank: 1 },
            ].map((row) => (
              <div key={row.field} className="flex items-center justify-between p-3 rounded-lg bg-white/[0.02] border border-white/[0.05]">
                <span className="text-slate-300">{row.field}</span>
                <span className="text-gold font-bold">{row.authority}</span>
              </div>
            ))}
          </div>
        </div>
      </AurixCard>
    );
  }

  if (subdomainId === 'reconciliation') {
    return <ReconciliationMatrix />;
  }

  // 'ingestion' and 'quality' route to dedicated pages; this is a graceful
  // fallback in case someone lands here directly via the query-param path.
  const subdomain = DOMAIN_REGISTRY['data-integrations']?.subdomains.find((s) => s.id === subdomainId);
  return (
    <AurixCard title={subdomain?.title || 'DATA & INTEGRATIONS'} badge={<AurixBadge variant="gold">DEDICATED WORKSPACE</AurixBadge>}>
      <div className="py-10 flex flex-col items-center justify-center text-center gap-4 font-mono text-xs text-slate-400">
        <p>This workspace lives at its own dedicated route for deep-linking and audit clarity.</p>
        {subdomain?.route && (
          <Link href={subdomain.route}>
            <AurixButton variant="primary" size="sm">OPEN {subdomain.title.toUpperCase()}</AurixButton>
          </Link>
        )}
      </div>
    </AurixCard>
  );
}

export default function DataIntegrationsPage() {
  return (
    <DomainWorkspaceOrchestrator
      domainKey="data-integrations"
      renderWorkspace={(subdomainId) => <DataIntegrationsWorkspace subdomainId={subdomainId} />}
    />
  );
}
