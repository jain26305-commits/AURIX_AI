'use client';

import React, { useState } from 'react';
import { MonthlyDataPoint } from '@/types/eda.types';

interface AurixTimeSeriesChartProps {
  data: MonthlyDataPoint[];
  title?: string;
  metricLabel?: string;
  valuePrefix?: string;
  accentColor?: 'blue' | 'gold';
  height?: number;
}

export const AurixTimeSeriesChart: React.FC<AurixTimeSeriesChartProps> = ({
  data,
  title,
  metricLabel = 'Units Demanded',
  valuePrefix = '',
  accentColor = 'blue',
  height = 240,
}) => {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  if (!data || data.length === 0) return null;

  const strokeColor = accentColor === 'gold' ? '#D4AF37' : '#D4AF37';
  const fillGradientId = `grad-${accentColor}`;

  const values = data.map((d) => d.demand);
  const maxVal = Math.max(...values, 1) * 1.15;
  const minVal = 0;

  const chartWidth = 700;
  const chartHeight = height;
  const paddingX = 40;
  const paddingY = 30;

  const effectiveWidth = chartWidth - paddingX * 2;
  const effectiveHeight = chartHeight - paddingY * 2;

  const points = data.map((item, index) => {
    const x = paddingX + (index / (data.length - 1)) * effectiveWidth;
    const y = chartHeight - paddingY - ((item.demand - minVal) / (maxVal - minVal)) * effectiveHeight;
    return { x, y, item };
  });

  // Construct smooth SVG Bezier path
  const pathD = points.reduce((acc, point, i, arr) => {
    if (i === 0) return `M ${point.x},${point.y}`;
    const prev = arr[i - 1];
    const cpx1 = prev.x + (point.x - prev.x) / 2;
    const cpy1 = prev.y;
    const cpx2 = prev.x + (point.x - prev.x) / 2;
    const cpy2 = point.y;
    return `${acc} C ${cpx1},${cpy1} ${cpx2},${cpy2} ${point.x},${point.y}`;
  }, '');

  const areaD = `${pathD} L ${points[points.length - 1].x},${chartHeight - paddingY} L ${points[0].x},${chartHeight - paddingY} Z`;

  return (
    <div className="w-full relative select-none">
      {title && (
        <div className="flex items-center justify-between pb-3 mb-2">
          <h4 className="text-xs font-mono font-bold tracking-wider text-white uppercase">{title}</h4>
          <span className="text-[10px] font-mono text-slate-400">12-MONTH HISTORICAL TRAJECTORY</span>
        </div>
      )}

      <div className="relative w-full overflow-hidden">
        <svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} className="w-full h-auto overflow-visible">
          <defs>
            <linearGradient id={fillGradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={strokeColor} stopOpacity="0.25" />
              <stop offset="100%" stopColor={strokeColor} stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Horizontal Grid lines */}
          {[0, 0.33, 0.66, 1].map((pct, i) => {
            const y = paddingY + pct * effectiveHeight;
            return (
              <line
                key={i}
                x1={paddingX}
                y1={y}
                x2={chartWidth - paddingX}
                y2={y}
                stroke="rgba(255,255,255,0.06)"
                strokeDasharray="4 4"
              />
            );
          })}

          {/* Area Fill */}
          <path d={areaD} fill={`url(#${fillGradientId})`} />

          {/* Trend Line */}
          <path d={pathD} fill="none" stroke={strokeColor} strokeWidth="2.5" strokeLinecap="round" />

          {/* Data Points */}
          {points.map((p, idx) => (
            <g key={idx} onMouseEnter={() => setHoveredIdx(idx)} onMouseLeave={() => setHoveredIdx(null)}>
              <circle
                cx={p.x}
                cy={p.y}
                r={hoveredIdx === idx ? 5 : 3.5}
                fill="#07090D"
                stroke={strokeColor}
                strokeWidth={hoveredIdx === idx ? 2.5 : 1.5}
                className="transition-all duration-150 cursor-pointer"
              />
            </g>
          ))}

          {/* X Axis Month Labels */}
          {points.map((p, idx) => (
            <text
              key={idx}
              x={p.x}
              y={chartHeight - 8}
              textAnchor="middle"
              className="text-[9px] font-mono fill-slate-500 font-medium"
            >
              {p.item.month}
            </text>
          ))}
        </svg>

        {/* Hover Crosshair Tooltip */}
        {hoveredIdx !== null && (
          <div
            className="absolute top-2 right-2 bg-[#15171A]/95 border border-white/20 rounded-lg p-2.5 shadow-2xl backdrop-blur-md pointer-events-none text-xs font-mono"
          >
            <div className="text-gold font-bold">{data[hoveredIdx].month} Observation</div>
            <div className="text-white mt-1">
              {metricLabel}: <span className="font-bold">{valuePrefix}{data[hoveredIdx].demand.toLocaleString()}</span>
            </div>
            <div className="text-slate-400 text-[10px]">
              Revenue: ₹{data[hoveredIdx].revenue.toLocaleString()}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};