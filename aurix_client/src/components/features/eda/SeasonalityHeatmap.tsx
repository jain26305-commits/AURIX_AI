'use client';

import React from 'react';
import { SeasonalityCell } from '@/types/eda.types';
import { Calendar } from 'lucide-react';

interface SeasonalityHeatmapProps {
  seasonality: SeasonalityCell[];
}

export const SeasonalityHeatmap: React.FC<SeasonalityHeatmapProps> = ({ seasonality }) => {
  return (
    <div className="w-full aurix-card-glass rounded-xl p-6 border border-white/[0.08]">
      <div className="flex items-center justify-between pb-4 mb-4 border-b border-white/[0.06]">
        <div>
          <h3 className="text-sm font-semibold text-white tracking-wide flex items-center gap-2">
            <Calendar className="w-4 h-4 text-[#D4AF37]" />
            12-MONTH SEASONALITY HEATMAP
          </h3>
          <p className="text-[11px] font-mono text-slate-400 mt-0.5">
            Normalized seasonal demand index across annualized operational cycles (1.0 = Baseline Mean).
          </p>
        </div>
      </div>

      <div className="grid grid-cols-3 sm:grid-cols-6 lg:grid-cols-12 gap-2 text-xs font-mono">
        {seasonality.map((cell) => {
          const isSurge = cell.averageIndex >= 1.2;
          const isNormal = cell.averageIndex >= 0.95 && cell.averageIndex < 1.2;

          return (
            <div
              key={cell.month}
              className={`p-3 rounded-lg border flex flex-col items-center justify-between text-center transition-all duration-200 ${
                isSurge
                  ? 'bg-gold/15 border-gold/50 text-gold shadow-[0_0_15px_rgba(212,175,55,0.15)]'
                  : isNormal
                  ? 'bg-[#B8912A]/15 border-[#D4AF37]/35 text-[#D4AF37]'
                  : 'bg-white/[0.02] border-white/[0.06] text-slate-400'
              }`}
            >
              <span className="font-bold text-white text-[11px]">{cell.month}</span>
              <span className="text-sm font-bold font-mono my-1.5">{cell.averageIndex.toFixed(2)}x</span>
              <span className="text-[9px] uppercase tracking-wider text-slate-400 truncate max-w-full">
                {cell.peakCategory}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};