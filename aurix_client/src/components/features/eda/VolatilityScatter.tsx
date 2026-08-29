'use client';

import React, { useState } from 'react';
import { SkuDemandProfile } from '@/types/eda.types';
import { Activity } from 'lucide-react';


interface VolatilityScatterProps {
  skuProfiles: SkuDemandProfile[];
  onSelectSku: (skuId: string) => void;
  selectedSkuId: string | null;
}

export const VolatilityScatter: React.FC<VolatilityScatterProps> = ({
  skuProfiles,
  onSelectSku,
  selectedSkuId,
}) => {
  const [hoveredSku, setHoveredSku] = useState<SkuDemandProfile | null>(null);

  const width = 600;
  const height = 220;
  const pad = 35;

  const maxDemand = Math.max(...skuProfiles.map((s) => s.meanMonthlyDemand), 10) * 1.15;
  const maxCV = 1.0;

  return (
    <div className="w-full aurix-card-glass rounded-xl p-6 border border-white/[0.08]">
      <div className="flex items-center justify-between pb-4 mb-4 border-b border-white/[0.06]">
        <div>
          <h3 className="text-sm font-semibold text-white tracking-wide flex items-center gap-2">
            <Activity className="w-4 h-4 text-[#F3B33D]" />
            DEMAND VOLUME VS. VOLATILITY SCATTER
          </h3>
          <p className="text-[11px] font-mono text-slate-400 mt-0.5">
            Distribution of Mean Monthly Volume (X) vs. Volatility CV (Y).
          </p>
        </div>
      </div>

      <div className="relative w-full overflow-hidden select-none">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto overflow-visible">
          {/* Grid lines */}
          <line x1={pad} y1={pad} x2={pad} y2={height - pad} stroke="rgba(255,255,255,0.15)" strokeWidth="1" />
          <line x1={pad} y1={height - pad} x2={width - pad} y2={height - pad} stroke="rgba(255,255,255,0.15)" strokeWidth="1" />

          {/* 30% and 70% Volatility Thresholds */}
          <line
            x1={pad}
            y1={height - pad - 0.3 * (height - pad * 2)}
            x2={width - pad}
            y2={height - pad - 0.3 * (height - pad * 2)}
            stroke="rgba(212,175,55,0.3)"
            strokeDasharray="4 4"
          />
          <line
            x1={pad}
            y1={height - pad - 0.7 * (height - pad * 2)}
            x2={width - pad}
            y2={height - pad - 0.7 * (height - pad * 2)}
            stroke="rgba(255,107,107,0.3)"
            strokeDasharray="4 4"
          />

          {/* Threshold Labels */}
          <text x={width - pad - 5} y={height - pad - 0.3 * (height - pad * 2) - 4} textAnchor="end" className="text-[8px] font-mono fill-[#D4AF37]">
            XYZ X/Y Cutoff (CV: 0.3)
          </text>
          <text x={width - pad - 5} y={height - pad - 0.7 * (height - pad * 2) - 4} textAnchor="end" className="text-[8px] font-mono fill-[#FF8585]">
            XYZ Y/Z Cutoff (CV: 0.7)
          </text>

          {/* SKU Scatter Points */}
          {skuProfiles.map((sku) => {
            const cx = pad + (sku.meanMonthlyDemand / maxDemand) * (width - pad * 2);
            const cy = height - pad - (sku.coefficientOfVariation / maxCV) * (height - pad * 2);
            const isSelected = sku.skuId === selectedSkuId;

            return (
              <g
                key={sku.skuId}
                onClick={() => onSelectSku(sku.skuId)}
                onMouseEnter={() => setHoveredSku(sku)}
                onMouseLeave={() => setHoveredSku(null)}
                className="cursor-pointer"
              >
                <circle
                  cx={cx}
                  cy={cy}
                  r={isSelected ? 7 : 5}
                  fill={sku.abcClass === 'A' ? '#D4AF37' : sku.abcClass === 'B' ? '#D4AF37' : '#94A3B8'}
                  stroke="#030303"
                  strokeWidth="1.5"
                  className="transition-all duration-200 hover:scale-125"
                />
              </g>
            );
          })}
        </svg>

        {hoveredSku && (
          <div className="absolute top-2 right-2 bg-[#15171A]/95 border border-white/20 rounded-lg p-2 text-xs font-mono shadow-2xl backdrop-blur-md pointer-events-none">
            <div className="text-white font-bold">{hoveredSku.skuName}</div>
            <div className="text-gold text-[11px] mt-0.5">
              Class: {hoveredSku.abcClass}-{hoveredSku.xyzClass} | CV: {(hoveredSku.coefficientOfVariation * 100).toFixed(0)}%
            </div>
            <div className="text-slate-400 text-[10px]">
              Monthly Mean: {hoveredSku.meanMonthlyDemand} pcs
            </div>
          </div>
        )}
      </div>
    </div>
  );
};