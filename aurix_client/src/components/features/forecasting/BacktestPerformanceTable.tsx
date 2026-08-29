'use client';

import React from 'react';
import { CompetingModelResult } from '@/types/forecast.types';
import { Award } from 'lucide-react';
import { AurixBadge } from '@/components/ui/AurixBadge';

interface BacktestPerformanceTableProps {
  models: CompetingModelResult[];
}

export const BacktestPerformanceTable: React.FC<BacktestPerformanceTableProps> = ({ models }) => {
  return (
    <div className="w-full aurix-card-glass rounded-xl p-6 border border-white/[0.08]">
      <div className="flex items-center justify-between pb-4 mb-4 border-b border-white/[0.06]">
        <div>
          <h3 className="text-sm font-semibold text-white tracking-wide flex items-center gap-2">
            <Award className="w-4 h-4 text-gold" />
            BACKTEST MODEL COMPETITION & LEADERBOARD
          </h3>
          <p className="text-[11px] font-mono text-slate-400 mt-0.5">
            Validation error metrics across 5 competing deterministic & ML algorithms.
          </p>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs font-mono">
          <thead>
            <tr className="border-b border-white/[0.08] text-slate-500 text-[10px] uppercase tracking-wider">
              <th className="pb-3 pl-2">Model Architecture</th>
              <th className="pb-3">WAPE Error</th>
              <th className="pb-3">RMSE</th>
              <th className="pb-3">MAE</th>
              <th className="pb-3">Residual Bias</th>
              <th className="pb-3">Fit P-Value</th>
              <th className="pb-3 text-right pr-2">Outcome</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.04]">
            {models.map((m) => (
              <tr
                key={m.modelName}
                className={`transition-colors ${
                  m.isChampion ? 'bg-gold/[0.04] text-white font-semibold' : 'hover:bg-white/[0.02] text-slate-300'
                }`}
              >
                <td className="py-3 pl-2 flex items-center gap-2">
                  {m.isChampion && <span className="w-1.5 h-1.5 rounded-full bg-gold" />}
                  <span>{m.modelName}</span>
                </td>
                <td className="py-3">
                  <span className={m.isChampion ? 'text-[#3DDB91] font-bold' : 'text-slate-300'}>
                    {m.wapePercent.toFixed(1)}%
                  </span>
                </td>
                <td className="py-3 text-slate-400">{m.rmse.toFixed(1)}</td>
                <td className="py-3 text-slate-400">{m.mae.toFixed(1)}</td>
                <td className="py-3">
                  <span className={Math.abs(m.bias) < 1.0 ? 'text-[#3DDB91]' : 'text-gold'}>
                    {m.bias > 0 ? `+${m.bias}` : m.bias}
                  </span>
                </td>
                <td className="py-3 text-slate-400">{m.fitPValue.toFixed(2)}</td>
                <td className="py-3 text-right pr-2">
                  {m.isChampion ? (
                    <AurixBadge variant="gold">SELECTED CHAMPION</AurixBadge>
                  ) : (
                    <span className="text-slate-500 text-[10px]">CANDIDATE</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};