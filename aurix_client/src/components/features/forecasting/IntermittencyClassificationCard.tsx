'use client';

import React from 'react';
import { IntermittencyMetrics } from '@/types/forecast.types';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { Target } from 'lucide-react';

interface IntermittencyClassificationCardProps {
  metrics?: IntermittencyMetrics;
  skuName?: string;
}

export const IntermittencyClassificationCard: React.FC<IntermittencyClassificationCardProps> = ({
  metrics = {
    averageDemandIntervalAdi: 1.48,
    coefficientOfVariationSquaredCv2: 0.62,
    patternClass: 'LUMPY',
    syntetosBoylanRecommendedModel: 'Croston Intermittent',
    classificationRationale:
      'High intermittency (ADI > 1.32) combined with high demand size variance (CV² > 0.49). Requires specialized intermittent smoothing to prevent over-buffering safety stock.',
  },
  skuName = 'Active SKU',
}) => {
  const isSmooth = metrics.patternClass === 'SMOOTH';
  const isLumpy = metrics.patternClass === 'LUMPY';

  // Normalize point for a 0-100 visual scatter space
  // ADI: 1.0 to 2.5 (Threshold at 1.32 ~ 35%)
  // CV²: 0.0 to 1.5 (Threshold at 0.49 ~ 45%)
  const xPos = Math.min(Math.max(((metrics.averageDemandIntervalAdi - 1.0) / 1.5) * 100, 10), 90);
  const yPos = Math.min(Math.max((1 - metrics.coefficientOfVariationSquaredCv2 / 1.5) * 100, 10), 90);

  return (
    <AurixCard
      title="DEMAND INTERMITTENCY & VOLATILITY MATRIX"
      badge={
        <AurixBadge variant={isSmooth ? 'success' : isLumpy ? 'danger' : 'warning'} pulse={isLumpy}>
          {metrics.patternClass} DEMAND
        </AurixBadge>
      }
    >
      <div className="space-y-4 pt-1 font-mono text-xs select-none">
        {/* Quadrant Visual Grid */}
        <div className="h-48 w-full relative bg-white/[0.01] border border-white/[0.06] rounded-xl overflow-hidden p-3">
          {/* Quadrant Threshold Guidelines */}
          <div className="absolute inset-x-0 top-[55%] border-b border-white/20 border-dashed pointer-events-none" />
          <div className="absolute inset-y-0 left-[35%] border-r border-white/20 border-dashed pointer-events-none" />

          {/* Quadrant Background Labels */}
          <div className="absolute top-2 left-2 text-[9px] text-slate-500 font-bold uppercase">
            ERRATIC (High CV², Low ADI)
          </div>
          <div className="absolute top-2 right-2 text-[9px] text-[#FF6B6B]/60 font-bold uppercase">
            LUMPY (High CV², High ADI)
          </div>
          <div className="absolute bottom-2 left-2 text-[9px] text-[#3DDB91]/60 font-bold uppercase">
            SMOOTH (Low CV², Low ADI)
          </div>
          <div className="absolute bottom-2 right-2 text-[9px] text-[#F3B33D]/60 font-bold uppercase">
            INTERMITTENT (Low CV², High ADI)
          </div>

          {/* Active SKU Scatter Point */}
          <div
            className="absolute -translate-x-1/2 -translate-y-1/2 flex items-center gap-1.5 transition-all duration-300"
            style={{ left: `${xPos}%`, top: `${yPos}%` }}
          >
            <div className="relative">
              <span className="w-3.5 h-3.5 rounded-full bg-[#D4AF37] block animate-ping opacity-75 absolute inset-0" />
              <div className="w-3.5 h-3.5 rounded-full bg-[#D4AF37] border-2 border-black relative flex items-center justify-center">
                <div className="w-1 h-1 rounded-full bg-black" />
              </div>
            </div>
            <span className="text-[10px] font-bold text-white bg-black/80 px-1.5 py-0.5 rounded border border-white/10 shadow-lg whitespace-nowrap">
              {skuName} (ADI: {metrics.averageDemandIntervalAdi.toFixed(2)}, CV²: {metrics.coefficientOfVariationSquaredCv2.toFixed(2)})
            </span>
          </div>
        </div>

        {/* Statistical Metrics Row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-3 rounded-lg bg-white/[0.02] border border-white/[0.04]">
          <div>
            <span className="text-slate-500 block text-[10px]">AVG DEMAND INTERVAL</span>
            <span className="text-white font-bold text-sm">{metrics.averageDemandIntervalAdi.toFixed(2)}</span>
            <span className="text-[9px] text-slate-500 block">Threshold: &lt; 1.32</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px]">COEFF OF VARIATION²</span>
            <span className="text-white font-bold text-sm">{metrics.coefficientOfVariationSquaredCv2.toFixed(2)}</span>
            <span className="text-[9px] text-slate-500 block">Threshold: &lt; 0.49</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px]">CLASSIFICATION</span>
            <span className="text-gold font-bold text-sm">{metrics.patternClass}</span>
            <span className="text-[9px] text-slate-500 block">Syntetos-Boylan Matrix</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px]">RECOMMENDED MODEL</span>
            <span className="text-[#3DDB91] font-bold text-sm truncate block">{metrics.syntetosBoylanRecommendedModel}</span>
            <span className="text-[9px] text-slate-500 block">Optimized Solver</span>
          </div>
        </div>

        {/* Classification Rationale Annotation */}
        <p className="text-[11px] font-mono text-slate-400 leading-relaxed bg-black/40 p-3 rounded-lg border border-white/[0.04] flex items-start gap-2">
          <Target className="w-4 h-4 text-gold shrink-0 mt-0.5" />
          <span>{metrics.classificationRationale}</span>
        </p>
      </div>
    </AurixCard>
  );
};
