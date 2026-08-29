'use client';

import React from 'react';
import { DataBoundary } from '@/components/states/DataBoundary';
import { useForecastEngine } from '@/hooks/useForecastEngine';
import { IntermittencyClassificationCard } from '@/components/features/forecasting/IntermittencyClassificationCard';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';

export default function DemandIntelligencePage() {
  const { data: forecastData, loading, reload } = useForecastEngine('SKU-001');

  const championModel = forecastData?.metadata.competingModels.find((m) => m.isChampion);

  return (
    <div className="space-y-6 animate-pure-fade">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl aurix-card-glass border border-white/[0.08]">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded bg-gold/10 border border-gold/30 text-gold text-[10px] font-bold tracking-widest uppercase">
              DEMAND INTELLIGENCE
            </span>
            <span className="text-sm font-bold text-white font-mono">SKU Demand Pattern & Segmentation Engine</span>
          </div>
          <p className="text-[11px] font-mono text-slate-400 mt-0.5">
            Syntetos-Boylan intermittency matrix, coefficient of variation (CV²), and average demand interval (ADI) analytics.
          </p>
        </div>
      </div>

      <DataBoundary
        isLoading={loading}
        isError={!loading && !forecastData}
        errorMessage="Failed to load demand intelligence and segmentation telemetry."
        onRetry={reload}
        loadingMessage="CLASSIFYING DEMAND PROFILES & INTERMITTENCY BANDS..."
      >
        {forecastData && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono">
              <AurixCard title="CLASSIFICATION PATTERN" badge={<AurixBadge variant="gold">SYNTHESIZED</AurixBadge>}>
                <div className="mt-2 text-xl font-bold text-white uppercase">{forecastData.metadata.intermittency?.patternClass || 'SMOOTH'}</div>
                <div className="text-[11px] text-slate-400 mt-1">
                  ADI: {forecastData.metadata.intermittency?.averageDemandIntervalAdi ?? 1.1} | CV²: {forecastData.metadata.intermittency?.coefficientOfVariationSquaredCv2 ?? 0.25}
                </div>
              </AurixCard>
              <AurixCard title="HISTORICAL TRAINING" badge={<AurixBadge variant="success">STABLE</AurixBadge>}>
                <div className="mt-2 text-xl font-bold text-[#3DDB91]">{forecastData.metadata.historicalMonthsTrained} Months</div>
                <div className="text-[11px] text-slate-400 mt-1">Trained on trailing ledger records</div>
              </AurixCard>
              <AurixCard title="CHAMPION MODEL" badge={<AurixBadge variant="gold">OPTIMIZED</AurixBadge>}>
                <div className="mt-2 text-xl font-bold text-white">{forecastData.metadata.modelFamily}</div>
                <div className="text-[11px] text-slate-400 mt-1">WAPE: {championModel?.wapePercent ?? forecastData.metadata.accuracyWape}%</div>
              </AurixCard>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {forecastData.metadata.intermittency && (
                <IntermittencyClassificationCard
                  metrics={forecastData.metadata.intermittency}
                  skuName={forecastData.metadata.skuName}
                />
              )}
              <AurixCard title="DEMAND DISTRIBUTION & ZERO-SALES FREQUENCY" badge={<AurixBadge variant="gold">ANALYTICS</AurixBadge>}>
                <div className="space-y-3 pt-2 font-mono text-xs">
                  <div className="flex justify-between border-b border-white/5 pb-2">
                    <span className="text-slate-400">ZERO-DEMAND PERIODS (%):</span>
                    <span className="text-white font-bold">14.2%</span>
                  </div>
                  <div className="flex justify-between border-b border-white/5 pb-2">
                    <span className="text-slate-400">DEMAND PEAK MAGNITUDE:</span>
                    <span className="text-white font-bold">3.4x Mean</span>
                  </div>
                  <div className="flex justify-between border-b border-white/5 pb-2">
                    <span className="text-slate-400">SEASONAL AMPLITUDE:</span>
                    <span className="text-gold font-bold">Moderate (18%)</span>
                  </div>
                  <p className="text-slate-400 font-sans leading-relaxed pt-2">
                    Items classified under intermittent or lumpy demand patterns are routed to Croston’s method or SBA (Syntetos-Boylan Approximation) to prevent safety stock inflation.
                  </p>
                </div>
              </AurixCard>
            </div>
          </div>
        )}
      </DataBoundary>
    </div>
  );
}
