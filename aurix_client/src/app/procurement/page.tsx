'use client';

import React from 'react';
import { DomainWorkspaceOrchestrator } from '@/components/domain/DomainWorkspaceOrchestrator';
import { useProcurement } from '@/hooks/useProcurement';
import { useSupplyIntelligence } from '@/hooks/useSupplyIntelligence';
import { ProcurementStatsBar } from '@/components/features/procurement/ProcurementStatsBar';
import { PurchaseOrderTable } from '@/components/features/procurement/PurchaseOrderTable';
import { AsnTracker } from '@/components/features/procurement/AsnTracker';
import { ThreeWayMatchCard } from '@/components/features/procurement/ThreeWayMatchCard';
import { SupplierRiskComparison } from '@/components/features/supply/SupplierRiskComparison';
import { SupplierScorecard } from '@/components/features/supply/SupplierScorecard';
import { LeadTimeDistributionCard } from '@/components/features/supply/LeadTimeDistributionCard';
import { DualSourcingRecommender } from '@/components/features/supply/DualSourcingRecommender';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { AurixButton } from '@/components/ui/AurixButton';
import { RotateCw, Search, Box } from 'lucide-react';

function ProcurementWorkspace({ subdomainId }: { subdomainId: string }) {
  const { data: procureData, loading: procureLoading, filteredOrders, filteredMatches, searchQuery, setSearchQuery, reload: reloadProcure } = useProcurement();
  const { data: supplyData, loading: supplyLoading, activeVendor, setSelectedVendorId } = useSupplyIntelligence();

  const isLoading = procureLoading || supplyLoading;
  const hasError = (!procureLoading && !procureData) || (!supplyLoading && !supplyData);

  if (isLoading) {
    return (
      <div className="py-24 flex flex-col items-center justify-center text-center space-y-4 font-mono">
        <div className="w-8 h-8 rounded-full border-2 border-gold border-t-transparent animate-spin" />
        <p className="text-xs text-slate-400 tracking-widest uppercase">CALCULATING SUPPLIER & SPEND POSTURE...</p>
      </div>
    );
  }

  if (hasError || !procureData || !supplyData) {
    return (
      <div className="py-12 text-center font-mono">
        <p className="text-sm text-white font-bold">Failed to load procurement intelligence.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <ProcurementStatsBar summary={procureData.summary} />

      {/* SUPPLIERS */}
      {subdomainId === 'suppliers' && (
        <div className="space-y-6 animate-pure-fade">
          {/* Active Supplier Selector */}
          <div className="flex flex-wrap gap-2 mb-4">
            {supplyData.suppliers.map((s) => (
              <AurixButton
                key={s.supplierId}
                variant={activeVendor?.supplierId === s.supplierId ? 'gold' : 'secondary'}
                size="sm"
                onClick={() => setSelectedVendorId(s.supplierId)}
              >
                <Box className="w-3.5 h-3.5 mr-1.5" />
                {s.supplierId}
              </AurixButton>
            ))}
          </div>

          {activeVendor && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <SupplierScorecard supplier={activeVendor} />
              <LeadTimeDistributionCard leadTime={activeVendor.leadTime} supplierName={activeVendor.supplierName} />
            </div>
          )}
        </div>
      )}

      {/* SPEND & PPV */}
      {subdomainId === 'spend' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-pure-fade">
          <AurixCard title="ACTIVE INBOUND SPEND BY VENDOR" badge={<AurixBadge variant="gold">TREEMAP</AurixBadge>}>
            <div className="space-y-2.5 pt-2 font-mono text-xs">
              {Array.from(new Set(procureData.purchaseOrders.map((po) => po.vendorName))).slice(0, 5).map((vendor) => {
                const total = procureData.purchaseOrders
                  .filter((po) => po.vendorName === vendor)
                  .reduce((sum, po) => sum + po.totalAmountINR, 0);
                const maxTotal = Math.max(...procureData.purchaseOrders.map((po) => po.totalAmountINR), 1) * 3;
                const pct = Math.min(100, Math.round((total / maxTotal) * 100));
                return (
                  <div key={vendor}>
                    <div className="flex justify-between mb-1">
                      <span className="text-slate-300 truncate">{vendor}</span>
                      <span className="text-white font-bold">₹{total.toLocaleString('en-IN')}</span>
                    </div>
                    <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
                      <div className="h-full bg-gradient-to-r from-gold/60 to-gold rounded-full" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </AurixCard>
          <AurixCard title="PURCHASE PRICE VARIANCE" badge={<AurixBadge variant="success">FAVORABLE</AurixBadge>}>
            <div className="pt-2 space-y-3 font-mono text-xs">
              <div className="flex justify-between border-b border-white/5 pb-2">
                <span className="text-slate-400">3-WAY MATCH PASS RATE</span>
                <span className="text-[#3DDB91] font-bold">{procureData.summary.threeWayMatchPassRatePercent}%</span>
              </div>
              <div className="flex justify-between border-b border-white/5 pb-2">
                <span className="text-slate-400">RECONCILED ORDERS (PERIOD)</span>
                <span className="text-white font-bold">{procureData.summary.reconciledOrdersCount}</span>
              </div>
              <p className="text-slate-400 font-sans leading-relaxed pt-1">
                Purchase price variance is tracked at the line-item level against standard cost baselines,
                with unfavorable variances routed to category buyers for renegotiation.
              </p>
            </div>
          </AurixCard>
        </div>
      )}

      {/* ORDERS */}
      {subdomainId === 'orders' && (
        <div className="space-y-4 animate-pure-fade">
          <div className="flex items-center justify-between gap-3">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
              <input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search PO number or vendor..."
                className="w-full bg-[#15171A] border border-white/10 rounded-lg pl-8 pr-3 py-1.5 text-white placeholder-slate-500 focus:outline-none focus:border-[#D4AF37]"
              />
            </div>
            <AurixButton variant="secondary" size="sm" onClick={reloadProcure}>
              <RotateCw className="w-3.5 h-3.5 mr-1.5" /> REFRESH
            </AurixButton>
          </div>
          <PurchaseOrderTable orders={filteredOrders} />
          <AsnTracker asns={procureData.asns} />
        </div>
      )}

      {/* RISK */}
      {subdomainId === 'risk' && (
        <div className="space-y-6 animate-pure-fade">
          <SupplierRiskComparison suppliers={supplyData.suppliers} />
          <ThreeWayMatchCard matches={filteredMatches} />
          <DualSourcingRecommender recommendations={supplyData.dualSourcingRecommendations} />
        </div>
      )}
    </div>
  );
}

export default function ProcurementPage() {
  return (
    <DomainWorkspaceOrchestrator
      domainKey="procurement"
      renderWorkspace={(subdomainId) => <ProcurementWorkspace subdomainId={subdomainId} />}
    />
  );
}
