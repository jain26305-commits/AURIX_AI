'use client';

import React from 'react';
import { ForecastHorizon } from '@/types/forecast.types';


interface ForecastHorizonSelectorProps {
  selectedHorizon: ForecastHorizon;
  onSelectHorizon: (h: ForecastHorizon) => void;
}

export const ForecastHorizonSelector: React.FC<ForecastHorizonSelectorProps> = ({
  selectedHorizon,
  onSelectHorizon,
}) => {
  const horizons: { key: ForecastHorizon; label: string; sub: string }[] = [
    { key: '1M', label: '1 MONTH', sub: '30 Days (Tactical Replenishment)' },
    { key: '3M', label: '3 MONTHS', sub: '90 Days (Standard Procurement)' },
    { key: '6M', label: '6 MONTHS', sub: '180 Days (Strategic Production)' },
    { key: '12M', label: '12 MONTHS', sub: 'Annual Capacity Planning' },
  ];

  return (
    <div className="flex items-center gap-2 p-1 bg-[#15171A] border border-white/10 rounded-xl text-xs font-mono">
      {horizons.map((h) => (
        <button
          key={h.key}
          onClick={() => onSelectHorizon(h.key)}
          className={`px-3 py-1.5 rounded-lg transition-all duration-200 cursor-pointer font-bold ${
            selectedHorizon === h.key
              ? 'bg-gold/20 text-gold border border-gold/40 shadow-[0_0_12px_rgba(212,175,55,0.2)]'
              : 'text-slate-400 hover:text-white hover:bg-white/[0.04]'
          }`}
          title={h.sub}
        >
          {h.label}
        </button>
      ))}
    </div>
  );
};