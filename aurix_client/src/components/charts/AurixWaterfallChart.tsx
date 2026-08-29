'use client';

import React from 'react';
import { WorkingCapitalWaterfallItem } from '@/types/finance.types';

interface AurixWaterfallChartProps {
  items: WorkingCapitalWaterfallItem[];
  height?: number;
}

interface WaterfallBar {
  item: WorkingCapitalWaterfallItem;
  x: number;
  y: number;
  barH: number;
  runningTotal: number;
}

export const AurixWaterfallChart: React.FC<AurixWaterfallChartProps> = ({
  items,
  height = 240,
}) => {
  if (!items || items.length === 0) return null;

  const width = 760;
  const paddingX = 40;
  const paddingY = 30;
  const effectiveWidth = width - paddingX * 2;
  const effectiveHeight = height - paddingY * 2;

  const barWidth = effectiveWidth / items.length - 24;
  const maxVal =
    Math.max(...items.map((item) => Math.abs(item.amountINR))) * 1.15;

  const bars = items.reduce<WaterfallBar[]>((acc, item, idx) => {
    const x =
      paddingX +
      idx * (effectiveWidth / items.length) +
      12;

    const barH =
      (Math.abs(item.amountINR) / maxVal) * effectiveHeight;

    const previousTotal = acc.length > 0
      ? acc[acc.length - 1].runningTotal
      : 0;

    let y: number;
    let runningTotal: number;

    if (item.type === 'base' || item.type === 'total') {
      y = height - paddingY - barH;
      runningTotal = item.amountINR;
    } else if (item.type === 'negative') {
      const startY =
        height -
        paddingY -
        (previousTotal / maxVal) * effectiveHeight;

      y = startY;
      runningTotal = previousTotal + item.amountINR;
    } else {
      y = height - paddingY - barH;
      runningTotal = previousTotal + item.amountINR;
    }

    acc.push({
      item,
      x,
      y,
      barH,
      runningTotal,
    });

    return acc;
  }, []);

  return (
    <div className="w-full aurix-card-glass rounded-xl p-6 border border-white/[0.08] select-none">
      <div className="flex items-center justify-between pb-4 mb-3 border-b border-white/[0.06]">
        <div>
          <h3 className="text-sm font-semibold text-white tracking-wide">
            WORKING CAPITAL EXPOSURE & UNLOCK BRIDGE
          </h3>
          <p className="text-[11px] font-mono text-slate-400 mt-0.5">
            Sequential capital allocation from gross inventory position to optimized holding target.
          </p>
        </div>
      </div>

      <div className="relative w-full overflow-hidden">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-auto overflow-visible"
        >
          {/* Base Grid */}
          <line
            x1={paddingX}
            y1={height - paddingY}
            x2={width - paddingX}
            y2={height - paddingY}
            stroke="rgba(255,255,255,0.15)"
          />

          {bars.map(({ item, x, y, barH }) => {
            const fill =
              item.type === 'base'
                ? '#D4AF37'
                : item.type === 'negative'
                  ? '#FF6B6B'
                  : item.type === 'positive'
                    ? '#3DDB91'
                    : '#D4AF37';

            return (
              <g
                key={item.category}
                className="transition-all duration-300 group"
              >
                <rect
                  x={x}
                  y={y}
                  width={barWidth}
                  height={Math.max(barH, 4)}
                  fill={fill}
                  rx={4}
                  className="opacity-85 hover:opacity-100 transition-opacity"
                />

                {/* Amount Label */}
                <text
                  x={x + barWidth / 2}
                  y={y - 6}
                  textAnchor="middle"
                  className="text-[9px] font-mono font-bold fill-white"
                >
                  ₹{(Math.abs(item.amountINR) / 100000).toFixed(1)}L
                </text>

                {/* Category Label */}
                <text
                  x={x + barWidth / 2}
                  y={height - paddingY + 14}
                  textAnchor="middle"
                  className="text-[8px] font-mono fill-slate-400 font-medium"
                >
                  {item.category}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
};