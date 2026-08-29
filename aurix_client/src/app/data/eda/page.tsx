'use client';

import React, { useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { PortfolioMetricsBar } from '@/components/features/eda/PortfolioMetricsBar';
import { SkuSegmentationGrid } from '@/components/features/eda/SkuSegmentationGrid';
import { SeasonalityHeatmap } from '@/components/features/eda/SeasonalityHeatmap';
import { VolatilityScatter } from '@/components/features/eda/VolatilityScatter';
import { AurixTimeSeriesChart } from '@/components/charts/AurixTimeSeriesChart';
import { useEdaAnalytics } from '@/hooks/useEdaAnalytics';
import { AurixButton } from '@/components/ui/AurixButton';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { ArrowRight } from 'lucide-react';
import { useWorkspaceHeader } from '@/context/WorkspaceHeaderContext';

export default function EdaPage() {
  const [selectedAbc, setSelectedAbc] = useState<string | null>(null);
  const [selectedXyz, setSelectedXyz] = useState<string | null>(null);

  const router = useRouter();

  const {
    report,
    loading,
    categories,
    selectedCategory,
    setSelectedCategory,
    filteredSkus,
    selectedSkuId,
    setSelectedSkuId,
    activeSkuProfile,
  } = useEdaAnalytics();

  useWorkspaceHeader({
    activeWorkspaceTitle: 'EDA Workspace',
    activeSku: activeSkuProfile?.skuId,
  });

  const segmentedSkus = useMemo(() => {
    if (!selectedAbc && !selectedXyz) {
      return filteredSkus;
    }

    return filteredSkus.filter((sku) => {
      const abcMatch = !selectedAbc || sku.abcClass === selectedAbc;
      const xyzMatch = !selectedXyz || sku.xyzClass === selectedXyz;
      return abcMatch && xyzMatch;
    });
  }, [filteredSkus, selectedAbc, selectedXyz]);

  const handleSegmentationSelect = (abc: string, xyz: string) => {
    setSelectedAbc(abc);
    setSelectedXyz(xyz);

    const firstMatchingSku = filteredSkus.find(
      (sku) => sku.abcClass === abc && sku.xyzClass === xyz
    );

    if (firstMatchingSku) {
      setSelectedSkuId(firstMatchingSku.skuId);
    }
  };

  if (loading || !report) {
    return (
      <div className="py-24 flex flex-col items-center justify-center text-center space-y-4">
        <div className="w-8 h-8 rounded-full border-2 border-[#D4AF37] border-t-transparent animate-spin" />
        <p className="text-xs font-mono text-slate-400 tracking-widest uppercase">
          COMPUTING PORTFOLIO DISTRIBUTIONS & SEGMENTATION...
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-pure-fade">
      {/* Workspace Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white tracking-wide">
            EXPLORATORY DEMAND ANALYSIS
          </h1>

          <p className="text-xs font-mono text-slate-400 mt-1">
            Portfolio clustering, ABC/XYZ variance mapping, and seasonality discovery.
          </p>

          {(selectedAbc || selectedXyz) && (
            <div className="flex items-center gap-2 mt-3">
              <AurixBadge variant="gold">
                SEGMENT: {selectedAbc ?? 'ALL'}-{selectedXyz ?? 'ALL'}
              </AurixBadge>

              <button
                type="button"
                onClick={() => {
                  setSelectedAbc(null);
                  setSelectedXyz(null);
                }}
                className="text-[10px] font-mono text-slate-500 hover:text-white transition-colors"
              >
                CLEAR
              </button>
            </div>
          )}
        </div>

        <div className="flex items-center gap-3">
          <AurixButton
            variant="gold"
            size="sm"
            onClick={() =>
              router.push('/supply-chain?subdomain=demand-forecast')
            }
          >
            <span>PROCEED TO FORECASTING</span>
            <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
          </AurixButton>
        </div>
      </div>

      {/* Top Telemetry Metrics */}
      <PortfolioMetricsBar summary={report.summary} />

      {/* Primary Analytical Dual-Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column */}
        <div className="lg:col-span-7 space-y-6">
          <AurixCard
            title="SKU TRAJECTORY & PROVENANCE INSPECTOR"
            badge={
              activeSkuProfile && (
                <AurixBadge variant="gold">
                  {activeSkuProfile.abcClass}-{activeSkuProfile.xyzClass} CLASS
                </AurixBadge>
              )
            }
          >
            {/* Category and SKU Selector */}
            <div className="flex flex-wrap items-center gap-3 pb-4 mb-4 border-b border-white/[0.06] text-xs font-mono">
              <select
                value={selectedCategory}
                onChange={(e) => {
                  setSelectedCategory(e.target.value);
                  setSelectedAbc(null);
                  setSelectedXyz(null);
                }}
                className="bg-[#15171A] border border-white/10 rounded-lg px-3 py-1.5 text-slate-200 font-mono focus:outline-none"
              >
                <option value="all">ALL CATEGORIES</option>

                {categories.map((category: string) => (
                  <option key={category} value={category}>
                    {category}
                  </option>
                ))}
              </select>

              <select
                value={selectedSkuId || ''}
                onChange={(e) => setSelectedSkuId(e.target.value)}
                className="bg-[#15171A] border border-white/10 rounded-lg px-3 py-1.5 text-slate-200 font-mono focus:outline-none flex-1"
              >
                {segmentedSkus.map((sku) => (
                  <option key={sku.skuId} value={sku.skuId}>
                    {sku.skuId} — {sku.skuName} ({sku.abcClass}-{sku.xyzClass})
                  </option>
                ))}
              </select>
            </div>

            {/* Curve Chart */}
            {activeSkuProfile && (
              <div className="space-y-4">
                <AurixTimeSeriesChart
                  data={activeSkuProfile.monthlyHistory}
                  metricLabel="Demand"
                  accentColor="blue"
                  height={220}
                />

                <div className="grid grid-cols-3 gap-3 pt-3 border-t border-white/[0.04] text-[11px] font-mono">
                  <div>
                    <span className="text-slate-500 block">TOTAL VOLUME:</span>
                    <span className="text-white font-bold">
                      {activeSkuProfile.totalVolume.toLocaleString()} pcs
                    </span>
                  </div>

                  <div>
                    <span className="text-slate-500 block">VOLATILITY (CV):</span>
                    <span className="text-gold font-bold">
                      {(activeSkuProfile.coefficientOfVariation * 100).toFixed(1)}%
                    </span>
                  </div>

                  <div>
                    <span className="text-slate-500 block">PATTERN:</span>
                    <span className="text-[#3DDB91] font-bold">
                      {activeSkuProfile.demandPattern}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </AurixCard>

          <SeasonalityHeatmap seasonality={report.seasonality} />
        </div>

        {/* Right Column */}
        <div className="lg:col-span-5 space-y-6">
          <SkuSegmentationGrid
            skuProfiles={report.skuProfiles}
            onSelectCell={handleSegmentationSelect}
          />

          <VolatilityScatter
            skuProfiles={report.skuProfiles}
            onSelectSku={(skuId) => setSelectedSkuId(skuId)}
            selectedSkuId={selectedSkuId}
          />
        </div>
      </div>
    </div>
  );
}