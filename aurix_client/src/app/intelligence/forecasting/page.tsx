'use client';

import React from 'react';
import { DataBoundary } from '@/components/states/DataBoundary';
import { useForecastEngine } from '@/hooks/useForecastEngine';
import { ForecastHorizonSelector } from '@/components/features/forecasting/ForecastHorizonSelector';
import { ChampionModelCard } from '@/components/features/forecasting/ChampionModelCard';
import { DemandForecastTimelineChart } from '@/components/features/forecasting/DemandForecastTimelineChart';
import { IntermittencyClassificationCard } from '@/components/features/forecasting/IntermittencyClassificationCard';
import { BacktestPerformanceTable } from '@/components/features/forecasting/BacktestPerformanceTable';
import { ModelTransparencyDrawer } from '@/components/features/forecasting/ModelTransparencyDrawer';
import { AurixBadge } from '@/components/ui/AurixBadge';

export default function ForecastingIntelligencePage() {
  const {
    data: forecastData,
    loading: forecastLoading,
    horizon,
    setHorizon,
    isDrawerOpen,
    setIsDrawerOpen,
    reload: reloadForecast,
  } = useForecastEngine('SKU-001');

  return (
    <div className="space-y-6 animate-pure-fade">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl aurix-card-glass border border-white/[0.08]">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded bg-gold/10 border border-gold/30 text-gold text-[10px] font-bold tracking-widest uppercase">
              INTELLIGENCE HUB
            </span>
            <span className="text-sm font-bold text-white font-mono">
              {forecastData?.metadata.skuName || 'Demand & Forecasting Engine'}
            </span>
            {forecastData && <AurixBadge variant="gold">{forecastData.metadata.skuId}</AurixBadge>}
          </div>
          <p className="text-[11px] font-mono text-slate-400 mt-0.5">
            Stochastic Monte Carlo forecasting with Syntetos-Boylan intermittency classification & champion model backtesting.
          </p>
        </div>

        {forecastData && (
          <ForecastHorizonSelector
            selectedHorizon={horizon}
            onSelectHorizon={setHorizon}
          />
        )}
      </div>

      <DataBoundary
        isLoading={forecastLoading}
        isError={!forecastLoading && !forecastData}
        errorMessage="Failed to load statistical demand forecasts and intermittency telemetry."
        onRetry={reloadForecast}
        loadingMessage="COMPUTING PROBABILISTIC DEMAND TRAJECTORIES & INTERMITTENCY SOLVERS..."
      >
        {forecastData && (
          <div className="space-y-6">
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

            <DemandForecastTimelineChart
              timeline={forecastData.timeline}
              skuName={forecastData.metadata.skuName}
            />

            <BacktestPerformanceTable models={forecastData.metadata.competingModels} />

            <ModelTransparencyDrawer
              metadata={forecastData.metadata}
              isOpen={isDrawerOpen}
              onClose={() => setIsDrawerOpen(false)}
            />
          </div>
        )}
      </DataBoundary>
    </div>
  );
}
