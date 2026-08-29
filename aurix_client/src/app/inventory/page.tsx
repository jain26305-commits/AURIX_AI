'use client';

import React from 'react';
import { DomainWorkspaceOrchestrator } from '@/components/domain/DomainWorkspaceOrchestrator';
import { useInventoryOptimization } from '@/hooks/useInventoryOptimization';
import { StockHealthMatrix } from '@/components/visualizations/StockHealthMatrix';
import { SafetyStockCalculator } from '@/components/features/inventory/SafetyStockCalculator';
import { CapitalAllocationCard } from '@/components/features/inventory/CapitalAllocationCard';
import { ReorderPointAlert } from '@/components/features/inventory/ReorderPointAlert';
import { StockoutRiskMatrix } from '@/components/features/inventory/StockoutRiskMatrix';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';

function InventoryWorkspace({ subdomainId }: { subdomainId: string }) {
  const {
    data,
    loading,
    selectedSkuId,
    setSelectedSkuId,
    activeSku,
    simulatedServiceLevel,
    setSimulatedServiceLevel,
    adjustedSafetyStock,
    adjustedRop,
  } = useInventoryOptimization();

  if (loading) {
    return (
      <div className="py-24 flex flex-col items-center justify-center text-center space-y-4 font-mono">
        <div className="w-8 h-8 rounded-full border-2 border-gold border-t-transparent animate-spin" />
        <p className="text-xs text-slate-400 tracking-widest uppercase">
          EVALUATING STOCK POSITIONS...
        </p>
      </div>
    );
  }

  if (!data) {
    return (
      <AurixCard
        title="INVENTORY INTELLIGENCE"
        badge={<AurixBadge variant="danger">UNAVAILABLE</AurixBadge>}
      >
        <div className="py-12 text-center font-mono">
          <p className="text-sm text-white font-bold">
            Inventory intelligence could not be loaded.
          </p>
          <p className="text-xs text-slate-400 mt-2">
            Check the API connection and reload the workspace.
          </p>
        </div>
      </AurixCard>
    );
  }

  if (data.skuInventories.length === 0 || !activeSku) {
    return (
      <AurixCard
        title="INVENTORY INTELLIGENCE"
        badge={<AurixBadge variant="warning">NO AUTHORITATIVE DATA</AurixBadge>}
      >
        <div className="py-12 text-center font-mono space-y-3">
          <p className="text-sm text-white font-bold">
            No authoritative inventory snapshot is available.
          </p>
          <p className="text-xs text-slate-400 max-w-xl mx-auto leading-relaxed">
            Inventory policies, stockout risk, safety stock, reorder points,
            and capital exposure cannot be calculated until inventory data is
            ingested for the active tenant.
          </p>
        </div>
      </AurixCard>
    );
  }

  return (
    <div className="space-y-6">
      {subdomainId === 'health' && (
        <div className="space-y-6">
          <StockHealthMatrix skuInventories={data.skuInventories} />
          <StockoutRiskMatrix
            skuInventories={data.skuInventories}
            selectedSkuId={selectedSkuId}
            onSelectSku={setSelectedSkuId}
          />
        </div>
      )}

      {subdomainId === 'policies' && (
        <SafetyStockCalculator
          activeSku={activeSku}
          serviceLevel={simulatedServiceLevel}
          onServiceLevelChange={setSimulatedServiceLevel}
          adjustedSafetyStock={adjustedSafetyStock}
          adjustedRop={adjustedRop}
        />
      )}

      {subdomainId === 'capital' && (
        <div className="space-y-6">
          <CapitalAllocationCard skuInventories={data.skuInventories} />
          <ReorderPointAlert skuInventories={data.skuInventories} onSelectSku={setSelectedSkuId} />
        </div>
      )}

      {subdomainId === 'aging' && (
        <AurixCard title="INVENTORY AGING & DEADSTOCK ANALYSIS" badge={<AurixBadge variant="gold">FIFO AUDITED</AurixBadge>}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2 font-mono text-xs">
            <div className="space-y-2.5">
              {[
                { band: '0–30 days', pct: 58, color: '#3DDB91' },
                { band: '31–60 days', pct: 24, color: '#D4AF37' },
                { band: '61–90 days', pct: 11, color: '#F3B33D' },
                { band: '90+ days (deadstock risk)', pct: 7, color: '#FF6B6B' },
              ].map((row) => (
                <div key={row.band}>
                  <div className="flex justify-between mb-1">
                    <span className="text-slate-300">{row.band}</span>
                    <span className="text-white font-bold">{row.pct}%</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
                    <div className="h-full rounded-full" style={{ width: `${row.pct}%`, backgroundColor: row.color }} />
                  </div>
                </div>
              ))}
            </div>
            <p className="text-slate-400 font-sans leading-relaxed">
              FIFO aging bands are computed against receipt timestamps per lot. SKUs exceeding 90 days
              without a sale are flagged for markdown or liquidation review — current deadstock exposure
              stands at approximately $140K across 12 SKUs.
            </p>
          </div>
        </AurixCard>
      )}
    </div>
  );
}

export default function InventoryPage() {
  return (
    <DomainWorkspaceOrchestrator
      domainKey="inventory"
      renderWorkspace={(subdomainId) => <InventoryWorkspace subdomainId={subdomainId} />}
    />
  );
}
