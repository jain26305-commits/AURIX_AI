'use client';

import React, { useState } from 'react';
import { ForecastTimelinePoint } from '@/types/forecast.types';

interface AurixForecastBandsProps {
  timeline: ForecastTimelinePoint[];
  height?: number;
}

export const AurixForecastBands: React.FC<AurixForecastBandsProps> = ({ timeline, height = 300 }) => {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  if (!timeline || timeline.length === 0) return null;

  const width = 800;
  const paddingX = 50;
  const paddingY = 40;
  const effectiveWidth = width - paddingX * 2;
  const effectiveHeight = height - paddingY * 2;

  // Compute scale boundaries
  const allValues: number[] = [];
  timeline.forEach((t) => {
    if (t.actual !== null && t.actual !== undefined) allValues.push(t.actual);
    if (t.forecast !== null && t.forecast !== undefined) allValues.push(t.forecast);
    if (t.lowerBound !== null && t.lowerBound !== undefined) allValues.push(t.lowerBound);
    if (t.upperBound !== null && t.upperBound !== undefined) allValues.push(t.upperBound);
  });

  const maxVal = Math.max(...allValues, 10) * 1.15;
  const minVal = 0;

  const points = timeline.map((item, index) => {
    const x = paddingX + (index / (timeline.length - 1)) * effectiveWidth;
    const yActual =
      item.actual !== null && item.actual !== undefined
        ? height - paddingY - ((item.actual - minVal) / (maxVal - minVal)) * effectiveHeight
        : null;
    const yForecast =
      item.forecast !== null && item.forecast !== undefined
        ? height - paddingY - ((item.forecast - minVal) / (maxVal - minVal)) * effectiveHeight
        : null;
    const yLower =
      item.lowerBound !== null && item.lowerBound !== undefined
        ? height - paddingY - ((item.lowerBound - minVal) / (maxVal - minVal)) * effectiveHeight
        : null;
    const yUpper =
      item.upperBound !== null && item.upperBound !== undefined
        ? height - paddingY - ((item.upperBound - minVal) / (maxVal - minVal)) * effectiveHeight
        : null;

    return { x, yActual, yForecast, yLower, yUpper, item };
  });

  // Split history vs forecast points
  const historyPoints = points.filter((p) => p.yActual !== null);
  const forecastPoints = points.filter((p) => p.yForecast !== null);
  const bandPoints = points.filter((p) => p.yLower !== null && p.yUpper !== null);

  // Link the last historical point to the first forecast point
  const lastHistory = historyPoints[historyPoints.length - 1];
  const fullForecastPathPoints = lastHistory ? [{ x: lastHistory.x, y: lastHistory.yActual }, ...forecastPoints.map(p => ({ x: p.x, y: p.yForecast }))] : [];

  // Historical Bezier Path
  const historyPathD = historyPoints.reduce((acc, point, i, arr) => {
    if (i === 0) return `M ${point.x},${point.yActual}`;
    const prev = arr[i - 1];
    const cpx1 = prev.x + (point.x - prev.x) / 2;
    const cpy1 = prev.yActual!;
    const cpx2 = prev.x + (point.x - prev.x) / 2;
    const cpy2 = point.yActual!;
    return `${acc} C ${cpx1},${cpy1} ${cpx2},${cpy2} ${point.x},${point.yActual}`;
  }, '');

  // Forecast Bezier Path
  const forecastPathD = fullForecastPathPoints.reduce((acc, point, i, arr) => {
    if (i === 0) return `M ${point.x},${point.y}`;
    const prev = arr[i - 1];
    const cpx1 = prev.x + (point.x - prev.x) / 2;
    const cpy1 = prev.y!;
    const cpx2 = prev.x + (point.x - prev.x) / 2;
    const cpy2 = point.y!;
    return `${acc} C ${cpx1},${cpy1} ${cpx2},${cpy2} ${point.x},${point.y}`;
  }, '');

  // Uncertainty Polygon Band
  let bandPolygonD = '';
  if (bandPoints.length > 0 && lastHistory) {
    const upperPath = bandPoints.map((p) => `${p.x},${p.yUpper}`).join(' L ');
    const lowerPath = [...bandPoints].reverse().map((p) => `${p.x},${p.yLower}`).join(' L ');
    bandPolygonD = `M ${lastHistory.x},${lastHistory.yActual} L ${upperPath} L ${lowerPath} Z`;
  }

  return (
    <div className="w-full relative select-none aurix-card-glass rounded-xl p-6 border border-white/[0.08]">
      <div className="flex flex-wrap items-center justify-between pb-4 mb-2 border-b border-white/[0.06] gap-3">
        <div>
          <h3 className="text-sm font-semibold text-white tracking-wide flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-gold animate-signal-beacon" />
            CHAMPION PROJECTION & UNCERTAINTY BAND
          </h3>
          <p className="text-[11px] font-mono text-slate-400 mt-0.5">
            Out-of-sample prediction with P10–P90 confidence interval envelope.
          </p>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4 text-[10px] font-mono">
          <span className="flex items-center gap-1.5 text-slate-300">
            <span className="w-3 h-[2px] bg-[#D4AF37] rounded-full" /> Historical Demand
          </span>
          <span className="flex items-center gap-1.5 text-gold font-semibold">
            <span className="w-3 h-[2px] bg-gold rounded-full border-b border-dashed" /> ML Forecast
          </span>
          <span className="flex items-center gap-1.5 text-[#F0D878]/80">
            <span className="w-3 h-2 bg-gold/20 border border-gold/40 rounded-sm" /> 80% CI (P10-P90)
          </span>
        </div>
      </div>

      <div className="relative w-full overflow-hidden">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto overflow-visible">
          <defs>
            <linearGradient id="bandGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#D4AF37" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#D4AF37" stopOpacity="0.03" />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((pct, i) => {
            const y = paddingY + pct * effectiveHeight;
            return (
              <line
                key={i}
                x1={paddingX}
                y1={y}
                x2={width - paddingX}
                y2={y}
                stroke="rgba(255,255,255,0.06)"
                strokeDasharray="4 4"
              />
            );
          })}

          {/* Vertical Transition Line (Historical vs Forecast Boundary) */}
          {lastHistory && (
            <line
              x1={lastHistory.x}
              y1={paddingY}
              x2={lastHistory.x}
              y2={height - paddingY}
              stroke="rgba(212,175,55,0.4)"
              strokeDasharray="2 2"
            />
          )}

          {/* Uncertainty Band Polygon */}
          {bandPolygonD && <path d={bandPolygonD} fill="url(#bandGradient)" />}

          {/* Historical Actuals Curve */}
          <path d={historyPathD} fill="none" stroke="#D4AF37" strokeWidth="2.5" strokeLinecap="round" />

          {/* Forecast Projection Curve */}
          <path d={forecastPathD} fill="none" stroke="#D4AF37" strokeWidth="2.5" strokeDasharray="5 5" strokeLinecap="round" />

          {/* Data Points */}
          {points.map((p, idx) => {
            const isHistorical = p.item.isHistorical;
            const cy = isHistorical ? p.yActual! : p.yForecast!;
            const color = isHistorical ? '#D4AF37' : '#D4AF37';

            return (
              <g key={idx} onMouseEnter={() => setHoveredIdx(idx)} onMouseLeave={() => setHoveredIdx(null)}>
                <circle
                  cx={p.x}
                  cy={cy}
                  r={hoveredIdx === idx ? 5.5 : 3.5}
                  fill="#030303"
                  stroke={color}
                  strokeWidth={hoveredIdx === idx ? 2.5 : 1.5}
                  className="transition-all duration-150 cursor-pointer"
                />
              </g>
            );
          })}

          {/* Timeline Labels */}
          {points.map((p, idx) => (
            <text
              key={idx}
              x={p.x}
              y={height - 12}
              textAnchor="middle"
              className={`text-[9px] font-mono font-medium ${
                p.item.isHistorical ? 'fill-slate-500' : 'fill-gold font-bold'
              }`}
            >
              {p.item.period.split(' ')[0]}
            </text>
          ))}
        </svg>

        {/* Hover Crosshair Tooltip */}
        {hoveredIdx !== null && (
          <div className="absolute top-2 right-2 bg-[#15171A]/95 border border-white/20 rounded-xl p-3 shadow-2xl backdrop-blur-md pointer-events-none text-xs font-mono">
            <div className="text-white font-bold pb-1 border-b border-white/10 flex items-center justify-between gap-4">
              <span>{timeline[hoveredIdx].period}</span>
              <span className={timeline[hoveredIdx].isHistorical ? 'text-[#D4AF37]' : 'text-gold'}>
                {timeline[hoveredIdx].isHistorical ? 'ACTUAL' : 'PROJECTION'}
              </span>
            </div>

            {timeline[hoveredIdx].isHistorical ? (
              <div className="text-white font-bold mt-2">
                Demand: <span className="text-[#D4AF37]">{timeline[hoveredIdx].actual} pcs</span>
              </div>
            ) : (
              <div className="space-y-1 mt-2">
                <div className="text-white font-bold">
                  Forecast: <span className="text-gold">{timeline[hoveredIdx].forecast} pcs</span>
                </div>
                <div className="text-[10px] text-slate-400">
                  Confidence Band: [{timeline[hoveredIdx].lowerBound} — {timeline[hoveredIdx].upperBound}] pcs
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};