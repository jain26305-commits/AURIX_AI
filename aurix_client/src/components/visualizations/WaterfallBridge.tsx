'use client';

import React from 'react';

import { AurixCard } from '@/components/ui/AurixCard';

export interface WaterfallStep {
  label: string;
  value: number;
  deltaType: 'baseline' | 'positive' | 'negative' | 'subtotal';
  percentage?: string;
  category?: string;
}

export interface WaterfallBridgeProps {
  title: string;
  subtitle?: string;
  badgeText?: string;
  steps: WaterfallStep[];
  currencySymbol?: string;
  baseHeight?: number;
}

export const WaterfallBridge: React.FC<WaterfallBridgeProps> = ({
  title,
  subtitle,
  badgeText = 'FINANCIAL ENGINE',
  steps,
  currencySymbol = '$',
}) => {
  const maxValue = Math.max(...steps.map((s) => Math.abs(s.value)), 1);

  return (
    <AurixCard
        title={title}
        subtitle={subtitle}
        badge={badgeText ? <span className="text-[9px] font-mono text-[#D4AF37] border border-[#D4AF37]/20 bg-[#D4AF37]/[0.05] px-2 py-1 rounded-md">{badgeText}</span> : undefined}
        className="space-y-6"
      >
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3 items-end pt-4">
        {steps.map((step, idx) => {
          const isNegative = step.deltaType === 'negative';
          const isPositive = step.deltaType === 'positive';
          const isBaseline = step.deltaType === 'baseline' || step.deltaType === 'subtotal';
          const heightPercent = Math.max(Math.min((Math.abs(step.value) / maxValue) * 100, 100), 12);

          return (
            <div key={idx} className="flex flex-col items-center space-y-2 group">
              <span className="text-[10px] font-mono font-bold text-slate-300">
                {step.value >= 0 ? `${currencySymbol}${step.value.toLocaleString()}` : `-${currencySymbol}${Math.abs(step.value).toLocaleString()}`}
              </span>

              <div className="w-full h-32 flex items-end justify-center bg-white/[0.01] rounded-lg p-1">
                <div
                  style={{ height: `${heightPercent}%` }}
                  className={`w-full rounded transition-all duration-500 relative group-hover:brightness-125 ${
                    isBaseline
                      ? 'bg-gradient-to-t from-[#D4AF37]/40 to-[#D4AF37] border border-[#F0D878]/60 shadow-[0_0_15px_rgba(212,175,55,0.3)]'
                      : isPositive
                      ? 'bg-gradient-to-t from-[#3DDB91]/30 to-[#3DDB91] border border-[#3DDB91]/50 shadow-[0_0_12px_rgba(61,219,145,0.2)]'
                      : 'bg-gradient-to-t from-[#FF6B6B]/30 to-[#FF6B6B] border border-[#FF6B6B]/50 shadow-[0_0_12px_rgba(255,107,107,0.2)]'
                  }`}
                />
              </div>

              <div className="text-center">
                <span className="text-[9px] font-mono uppercase text-slate-400 block truncate max-w-[100px]" title={step.label}>
                  {step.label}
                </span>
                {step.percentage && (
                  <span className={`text-[8px] font-mono font-bold ${isPositive ? 'text-[#3DDB91]' : isNegative ? 'text-[#FF6B6B]' : 'text-[#D4AF37]'}`}>
                    {step.percentage}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </AurixCard>
  );
};
