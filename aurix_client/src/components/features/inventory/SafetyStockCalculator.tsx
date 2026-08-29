'use client';

import React from 'react';
import { SkuInventoryMetrics } from '@/types/inventory.types';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { Sliders, Shield } from 'lucide-react';

interface SafetyStockCalculatorProps {
  activeSku: SkuInventoryMetrics;
  serviceLevel: number;
  onServiceLevelChange: (val: number) => void;
  adjustedSafetyStock: number;
  adjustedRop: number;
}

export const SafetyStockCalculator: React.FC<SafetyStockCalculatorProps> = ({
  activeSku,
  serviceLevel,
  onServiceLevelChange,
  adjustedSafetyStock,
  adjustedRop,
}) => {
  return (
    <AurixCard
      title="DYNAMIC SAFETY STOCK & ROP POLICY ENGINE"
      badge={<AurixBadge variant="gold">DETERMINISTIC Z-SCORE</AurixBadge>}
    >
      <div className="space-y-6 text-xs font-mono">
        {/* Service Level Slider */}
        <div className="space-y-2 pb-4 border-b border-white/[0.06]">
          <div className="flex items-center justify-between">
            <span className="text-slate-300 font-semibold flex items-center gap-1.5">
              <Sliders className="w-3.5 h-3.5 text-gold" />
              TARGET SERVICE LEVEL (NON-STOCKOUT PROBABILITY):
            </span>
            <span className="text-base font-bold text-gold">{serviceLevel}%</span>
          </div>

          <input
            type="range"
            min="90"
            max="99"
            step="1"
            value={serviceLevel}
            onChange={(e) => onServiceLevelChange(Number(e.target.value))}
            className="w-full h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer accent-gold focus:outline-none"
          />

          <div className="flex justify-between text-[10px] text-slate-500 font-medium">
            <span>90% (Standard)</span>
            <span>95% (Enterprise Default)</span>
            <span>98% (High Availability)</span>
            <span>99% (Mission Critical)</span>
          </div>
        </div>

        {/* Calculated Thresholds Dual Display */}
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06] space-y-1">
            <span className="text-[10px] text-slate-500 uppercase block">COMPUTED SAFETY BUFFER</span>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-white font-mono">{adjustedSafetyStock}</span>
              <span className="text-slate-400 text-xs">pcs</span>
            </div>
            <span className="text-[10px] text-gold block">
              Z = {serviceLevel === 99 ? '2.33' : serviceLevel >= 98 ? '2.05' : serviceLevel >= 95 ? '1.65' : '1.28'} × σD × √L
            </span>
          </div>

          <div className="p-4 rounded-xl bg-[#B8912A]/10 border border-[#D4AF37]/30 space-y-1 shadow-[0_0_20px_rgba(212,175,55,0.1)]">
            <span className="text-[10px] text-[#D4AF37] uppercase block font-semibold">REORDER POINT (ROP)</span>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-white font-mono">{adjustedRop}</span>
              <span className="text-slate-400 text-xs">pcs</span>
            </div>
            <span className="text-[10px] text-slate-400 block">
              (Lead-Time Demand: {Math.round(activeSku.averageDailyDemand * activeSku.leadTimeDaysUsed)} pcs) + SS
            </span>
          </div>
        </div>

        {/* Operational Prescription */}
        <div className="p-3.5 rounded-lg bg-white/[0.03] border border-white/[0.06] flex items-start gap-2.5 text-[11px] leading-relaxed text-slate-300">
          <Shield className="w-4 h-4 text-[#3DDB91] shrink-0 mt-0.5" />
          <div>
            <span className="text-white font-bold block">AURIX INVENTORY RECOMMENDATION:</span>
            {activeSku.recommendationAction}
          </div>
        </div>
      </div>
    </AurixCard>
  );
};