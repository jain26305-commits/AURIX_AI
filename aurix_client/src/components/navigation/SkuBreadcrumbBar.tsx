'use client';

import React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ChevronRight, ArrowLeft, Layers } from 'lucide-react';
import { AurixBadge } from '@/components/ui/AurixBadge';

export interface SkuOption {
  id: string;
  name: string;
}

export type SkuHealthStatus = 'CRITICAL' | 'OPTIMAL' | 'WATCH' | string;

export interface SkuBreadcrumbBarProps {
  skuId: string;
  skuName?: string;
  category?: string;
  healthStatus?: SkuHealthStatus;
  availableSkus?: SkuOption[];
}

const DEFAULT_SKU_CATALOG: SkuOption[] = [
  { id: 'SKU-001', name: '101 Beige-L (T-Shirt)' },
  { id: 'SKU-002', name: '101 Beige-M (T-Shirt)' },
  { id: 'SKU-003', name: '102 Navy-L (Polo)' },
  { id: 'SKU-004', name: '103 Black-XXL (Hoodie)' },
  { id: 'SKU-005', name: '104 Olive-M (Jeans)' },
];

export const SkuBreadcrumbBar: React.FC<SkuBreadcrumbBarProps> = ({
  skuId,
  skuName,
  category = 'Apparel & Garments',
  healthStatus,
  availableSkus = DEFAULT_SKU_CATALOG,
}) => {
  const router = useRouter();

  const handleSkuChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const nextSkuId = e.target.value;
    if (nextSkuId && nextSkuId !== skuId) {
      router.push(`/workspace/sku/${nextSkuId}`);
    }
  };

  const getHealthBadgeVariant = (status?: string) => {
    switch (status?.toUpperCase()) {
      case 'CRITICAL':
        return 'danger';
      case 'WATCH':
        return 'warning';
      case 'OPTIMAL':
        return 'success';
      default:
        return 'gold';
    }
  };

  return (
    <div className="flex flex-wrap items-center justify-between gap-4 p-3.5 rounded-xl aurix-card-glass border border-white/[0.08] font-mono text-xs select-none">
      {/* Breadcrumb Hierarchy Trail */}
      <div className="flex items-center gap-2 text-slate-400">
        <Link
          href="/control-tower"
          className="flex items-center gap-1.5 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5 text-slate-500" />
          <span>CONTROL TOWER</span>
        </Link>

        <ChevronRight className="w-3.5 h-3.5 text-slate-600" />

        <Link
          href="/data/eda"
          className="hover:text-white transition-colors"
        >
          <span>MATERIALS</span>
        </Link>

        <ChevronRight className="w-3.5 h-3.5 text-slate-600" />

        <div className="flex items-center gap-2">
          <Layers className="w-3.5 h-3.5 text-gold" />
          <span className="text-white font-bold">{skuId}</span>
          {skuName && <span className="text-slate-400">({skuName})</span>}
          <AurixBadge variant="gold">{category}</AurixBadge>
          {healthStatus && (
            <AurixBadge
              variant={getHealthBadgeVariant(healthStatus)}
              pulse={healthStatus.toUpperCase() === 'CRITICAL'}
            >
              {healthStatus}
            </AurixBadge>
          )}
        </div>
      </div>

      {/* Instant Material Switcher */}
      <div className="flex items-center gap-2.5">
        <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">
          SWITCH SKU:
        </span>
        <select
          value={skuId}
          onChange={handleSkuChange}
          className="bg-[#15171A] border border-white/15 rounded-lg px-3 py-1.5 text-white font-mono text-xs focus:outline-none focus:border-[#D4AF37] cursor-pointer"
        >
          {availableSkus.map((item) => (
            <option key={item.id} value={item.id} className="bg-[#0C0E12] text-slate-200">
              {item.id} — {item.name}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
};

export default SkuBreadcrumbBar;