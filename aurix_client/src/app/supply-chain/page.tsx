'use client';

import React from 'react';
import { DomainWorkspaceOrchestrator } from '@/components/domain/DomainWorkspaceOrchestrator';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { AurixButton } from '@/components/ui/AurixButton';
import { DataBoundary } from '@/components/states/DataBoundary';
import { useForecastEngine } from '@/hooks/useForecastEngine';
import { useNetworkTopology } from '@/hooks/useNetworkTopology';
import { ForecastHorizonSelector } from '@/components/features/forecasting/ForecastHorizonSelector';
import { ChampionModelCard } from '@/components/features/forecasting/ChampionModelCard';
import { DemandForecastTimelineChart } from '@/components/features/forecasting/DemandForecastTimelineChart';
import { IntermittencyClassificationCard } from '@/components/features/forecasting/IntermittencyClassificationCard';
import { BacktestPerformanceTable } from '@/components/features/forecasting/BacktestPerformanceTable';
import { ModelTransparencyDrawer } from '@/components/features/forecasting/ModelTransparencyDrawer';
import { NetworkTopologyGraph } from '@/components/features/network/NetworkTopologyGraph';
import { BullwhipAmplificationCard } from '@/components/features/network/BullwhipAmplificationCard';
import { SkuSelector } from '@/components/navigation/SkuSelector';

export default function SupplyChainPage() {
  const {
    data: forecastData,
    loading: forecastLoading,
    horizon,
    setHorizon,
    isDrawerOpen,
    setIsDrawerOpen,
    reload: reloadForecast,
  } = useForecastEngine();

  const {
    data: networkData,
    loading: networkLoading,
    reload: reloadNetwork,
  } = useNetworkTopology();

  return (
    <DomainWorkspaceOrchestrator
      domainKey="supply-chain"
      renderWorkspace={(subdomainId) => (
        <div className="space-y-6">
          {/* DEMAND & FORECAST INTELLIGENCE */}
          {subdomainId === 'demand-forecast' && (
            <DataBoundary
              isLoading={forecastLoading}
              isError={!forecastLoading && !forecastData}
              errorMessage="Failed to load statistical demand forecasts and intermittency telemetry."
              onRetry={reloadForecast}
              loadingMessage="COMPUTING PROBABILISTIC DEMAND TRAJECTORIES & INTERMITTENCY SOLVERS..."
            >
              {forecastData && (
                <div className="space-y-6 animate-pure-fade">
                  {/* Top Control Bar: Horizon Selector & Active SKU Context */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl aurix-card-glass border border-white/[0.08]">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-bold text-white font-mono">
                          {forecastData.metadata.skuName}
                        </span>
                        <AurixBadge variant="gold">{forecastData.metadata.skuId}</AurixBadge>
                      </div>
                      <p className="text-[11px] font-mono text-slate-400 mt-0.5">
                        Multi-horizon stochastic demand solver with Syntetos-Boylan intermittency classification.
                      </p>
                    </div>

                    <SkuSelector />

                    <ForecastHorizonSelector

                      selectedHorizon={horizon}
                      onSelectHorizon={setHorizon}
                    />
                  </div>

                  {/* Primary Visual Grid: Champion Certification & Intermittency Scatter */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <ChampionModelCard
                      metadata={forecastData.metadata}
                      onOpenTransparency={() => setIsDrawerOpen(true)}
                    />

                    <IntermittencyClassificationCard
                      metrics={forecastData.metadata.intermittency}
                      skuName={forecastData.metadata.skuName}
                    />
                  </div>

                  {/* Fan Chart: P10 / P50 / P90 Confidence Cone */}
                  <DemandForecastTimelineChart
                    timeline={forecastData.timeline}
                    skuName={forecastData.metadata.skuName}
                  />

                  {/* Model Competition Leaderboard */}
                  <BacktestPerformanceTable models={forecastData.metadata.competingModels} />

                  {/* Transparency & Explainability Drawer */}
                  <ModelTransparencyDrawer
                    metadata={forecastData.metadata}
                    isOpen={isDrawerOpen}
                    onClose={() => setIsDrawerOpen(false)}
                  />
                </div>
              )}
            </DataBoundary>
          )}

          {/* PLANNING */}
          {subdomainId === 'planning' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <AurixCard title="MULTI-ECHELON CAPACITY BALANCING" badge={<AurixBadge variant="gold">87.4% LOAD</AurixBadge>}>
                <p className="text-xs text-slate-400 font-sans leading-relaxed">
                  Constrained finite-capacity balancing across assembly and finishing work centers. Lead time safety buffers are dynamically scaled.
                </p>
              </AurixCard>
              <AurixCard title="BOTTLENECK SENSITIVITY" badge={<AurixBadge variant="danger">WC-04 SATURATED</AurixBadge>}>
                <p className="text-xs text-slate-400 font-sans leading-relaxed">
                  Stitching Work Center load projected to exceed 95% capacity in 14 days under baseline demand growth.
                </p>
              </AurixCard>
            </div>
          )}

          {/* REPLENISHMENT */}
          {subdomainId === 'replenishment' && (
            <AurixCard title="STOCHASTIC REPLENISHMENT SOLVER" badge={<AurixBadge variant="gold">38 POs PENDING</AurixBadge>}>
              <div className="space-y-4 pt-2 font-mono text-xs">
                <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.05] flex items-center justify-between">
                  <div>
                    <span className="text-white font-bold block">PO-2026-9812 â€¢ Yarn 100% Cotton 30s</span>
                    <span className="text-[10px] text-slate-500">Reorder Point: 1,200 kg | Order Qty: 4,000 kg</span>
                  </div>
                  <AurixButton variant="gold" size="sm">APPROVE DISPATCH</AurixButton>
                </div>
              </div>
            </AurixCard>
          )}

          {/* NETWORK */}
          {subdomainId === 'network' && (
            <DataBoundary
              isLoading={networkLoading}
              isError={!networkLoading && !networkData}
              errorMessage="Failed to load network topology graph and multi-echelon telemetry."
              onRetry={reloadNetwork}
              loadingMessage="SYNCHRONIZING TOPOLOGY GRAPH & MULTI-ECHELON NODES..."
            >
              {networkData && (
                <div className="space-y-6 animate-pure-fade">
                  <NetworkTopologyGraph
                    nodes={networkData.nodes}
                    edges={networkData.edges}
                  />
                  <BullwhipAmplificationCard
                    metrics={networkData.bullwhipMetrics}
                  />
                </div>
              )}
            </DataBoundary>
          )}
        </div>
      )}
    />
  );
}
