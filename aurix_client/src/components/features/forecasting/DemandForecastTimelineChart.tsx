'use client';

import React, { useMemo } from 'react';
import { ForecastTimelinePoint } from '@/types/forecast.types';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { TrendingUp } from 'lucide-react';

interface DemandForecastTimelineChartProps {
  timeline: ForecastTimelinePoint[];
  skuName?: string;
}

export const DemandForecastTimelineChart: React.FC<DemandForecastTimelineChartProps> = ({
  timeline,
  skuName = 'Active SKU',
}) => {
  const { points, maxValue, minValue } = useMemo(() => {
    if (!timeline || timeline.length === 0) {
      return { points: [], maxValue: 100, minValue: 0 };
    }

    const allValues = timeline.flatMap((p) => [
      p.actual ?? null,
      p.forecast ?? null,
      p.upperBound ?? null,
      p.lowerBound ?? null,
    ]).filter((v): v is number => v !== null);

    const max = Math.max(...allValues, 100);
    const min = Math.min(...allValues, 0);
    const range = max - min || 1;

    const mapped = timeline.map((p, idx) => {
      const x = (idx / (timeline.length - 1 || 1)) * 100;
      const getY = (val?: number | null) =>
        val !== undefined && val !== null ? 100 - ((val - min) / range) * 80 - 10 : null;

      return {
        ...p,
        x,
        yActual: getY(p.actual),
        yForecast: getY(p.forecast),
        yUpper: getY(p.upperBound),
        yLower: getY(p.lowerBound),
      };
    });

    return { points: mapped, maxValue: max, minValue: min };
  }, [timeline]);

  const historicalPoints = points.filter((p) => p.isHistorical && p.yActual !== null);
  const forecastPoints = points.filter((p) => !p.isHistorical && p.yForecast !== null);

  // SVG Path generation
  const actualPath = historicalPoints.reduce(
    (acc, p, idx) => `${acc} ${idx === 0 ? 'M' : 'L'} ${p.x} ${p.yActual}`,
    ''
  );

  const forecastPath = forecastPoints.reduce(
    (acc, p, idx) => `${acc} ${idx === 0 ? 'M' : 'L'} ${p.x} ${p.yForecast}`,
    ''
  );

  // Shaded cone area for P10 - P90 confidence bounds
  const conePoints = points.filter((p) => !p.isHistorical && p.yUpper !== null && p.yLower !== null);
  const upperPath = conePoints.map((p) => `${p.x},${p.yUpper}`).join(' ');
  const lowerPath = [...conePoints].reverse().map((p) => `${p.x},${p.yLower}`).join(' ');
  const confidenceConePolygon = conePoints.length > 0 ? `${upperPath} ${lowerPath}` : '';

  return (
    <AurixCard
      title="PROBABILISTIC DEMAND TRAJECTORY & FORECAST CONE"
      badge={<AurixBadge variant="gold">P10 / P50 / P90 STOCHASTIC CONE</AurixBadge>}
      headerAction={
        <div className="flex items-center gap-4 text-[10px] font-mono">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-0.5 bg-[#38BDF8]" />
            <span className="text-slate-400">HISTORICAL ACTUAL</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-0.5 bg-[#D4AF37] border-dashed" />
            <span className="text-white">P50 EXPECTED FORECAST</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 bg-[#D4AF37]/15 border border-[#D4AF37]/30 rounded-xs" />
            <span className="text-slate-400">80% CONFIDENCE INTERVAL (P10 - P90)</span>
          </div>
        </div>
      }
    >
      <div className="space-y-4 pt-2 select-none">
        {/* SVG Chart Container */}
        <div className="h-64 w-full relative bg-white/[0.01] border border-white/[0.05] rounded-xl p-4 overflow-hidden">
          {/* Y-Axis Guidelines */}
          <div className="absolute inset-x-4 inset-y-4 flex flex-col justify-between pointer-events-none opacity-20">
            <div className="border-b border-white/40 w-full" />
            <div className="border-b border-white/40 w-full" />
            <div className="border-b border-white/40 w-full" />
            <div className="border-b border-white/40 w-full" />
          </div>

          <svg className="w-full h-full overflow-visible" viewBox="0 0 100 100" preserveAspectRatio="none">
            {/* Shaded Confidence Cone */}
            {confidenceConePolygon && (
              <polygon
                points={confidenceConePolygon}
                fill="rgba(212, 175, 55, 0.12)"
                stroke="rgba(212, 175, 55, 0.3)"
                strokeWidth="0.5"
                strokeDasharray="1,1"
              />
            )}

            {/* Historical Actuals Line */}
            {actualPath && (
              <path
                d={actualPath}
                fill="none"
                stroke="#38BDF8"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            )}

            {/* Forecast Line */}
            {forecastPath && (
              <path
                d={forecastPath}
                fill="none"
                stroke="#D4AF37"
                strokeWidth="1.8"
                strokeDasharray="2,1"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            )}

            {/* Historical Actual Data Points */}
            {historicalPoints.map((p, i) => (
              <circle
                key={`act-${i}`}
                cx={p.x}
                cy={p.yActual!}
                r="1.2"
                fill="#38BDF8"
                className="hover:r-2 transition-all cursor-pointer"
              />
            ))}

            {/* Forecast Data Points */}
            {forecastPoints.map((p, i) => (
              <circle
                key={`fc-${i}`}
                cx={p.x}
                cy={p.yForecast!}
                r="1.4"
                fill="#D4AF37"
                className="hover:r-2.5 transition-all cursor-pointer"
              />
            ))}
          </svg>
        </div>

        {/* X-Axis Timeline Labels & Summary Footer */}
        <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 pt-1 border-t border-white/[0.04]">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-3.5 h-3.5 text-gold" />
            <span className="text-slate-400">{skuName} • Stochastic Trajectory Model</span>
          </div>
          <div className="flex items-center gap-6">
            <span>Range: {minValue.toFixed(0)} - {maxValue.toFixed(0)} units</span>
            <span>Horizon Points: {points.length}</span>
          </div>
        </div>
      </div>
    </AurixCard>
  );
};
