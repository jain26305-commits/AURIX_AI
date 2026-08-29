'use client';

import React from 'react';
import { DomainWorkspaceOrchestrator } from '@/components/domain/DomainWorkspaceOrchestrator';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { AurixButton } from '@/components/ui/AurixButton';
import Link from 'next/link';
import { DOMAIN_REGISTRY } from '@/config/domainRegistry';

export default function AdminPage() {
  return (
    <DomainWorkspaceOrchestrator
      domainKey="admin"
      renderWorkspace={(subdomainId) => {
        const subdomain = DOMAIN_REGISTRY.admin?.subdomains.find((s) => s.id === subdomainId);
        return (
          <AurixCard
            title="ADMIN & CONTROL"
            badge={<AurixBadge variant="success">RLS ENFORCED</AurixBadge>}
          >
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
      }}
    />
  );
}
