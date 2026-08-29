'use client';

import { useCallback, useMemo } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { DOMAIN_REGISTRY, DomainDefinition } from '@/config/domainRegistry';

export function useDomainNavigation(domainKey: string) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const domain = useMemo<DomainDefinition | undefined>(() => {
    return DOMAIN_REGISTRY[domainKey];
  }, [domainKey]);

  const activeSubdomainId = searchParams.get('subdomain');

  const selectSubdomain = useCallback(
    (subdomainId: string | null) => {
      if (!domain) return;
      if (subdomainId) {
        router.push(`${domain.route}?subdomain=${subdomainId}`, { scroll: false });
      } else {
        router.push(domain.route, { scroll: false });
      }
    },
    [domain, router]
  );

  const activeSubdomain = useMemo(() => {
    if (!domain || !activeSubdomainId) return null;
    return domain.subdomains.find((s) => s.id === activeSubdomainId) || null;
  }, [domain, activeSubdomainId]);

  return {
    domain,
    activeSubdomainId,
    activeSubdomain,
    selectSubdomain,
    isLanding: !activeSubdomainId,
  };
}
