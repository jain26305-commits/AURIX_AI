'use client';

import React from 'react';
import { BullwhipTierMetric } from '@/types/network.types';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { Activity, ArrowUpRight } from 'lucide-react';

interface BullwhipAmplificationCardProps {
  metrics: BullwhipTierMetric[];
}

export const BullwhipAmplificationCard: React.FC<BullwhipAmplificationCardProps> = ({ metrics }) => {
  return (
    <AurixCard
      title="MULTI-ECHELON BULLWHIP & DEMAND DISTORTION ANALYSIS"
      badge={<AurixBadge variant="gold">VARIANCE AMPLIFICATION (σ²)</AurixBadge>}
    >
      <div className="space-y-4 pt-2 font-mono text-xs select-none">
        <p className="text-[11px] text-slate-400 font-sans leading-relaxed">
          Quantifies order variance amplification across tiers relative to point-of-sale customer demand variance.
          A ratio &gt; 1.0 indicates structural demand distortion requiring buffer synchronization.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {metrics.map((tier) => {
            const isSevere = tier.distortionRisk === 'SEVERE';
            const isModerate = tier.distortionRisk === 'MODERATE';

            return (
              <div
                key={tier.tierName}
                className={`p-3.5 rounded-xl border transition-all ${
                  isSevere
                    ? 'bg-[#FF6B6B]/5 border-[#FF6B6B]/30'
                    : isModerate
                    ? 'bg-[#F3B33D]/5 border-[#F3B33D]/30'
                    : 'bg-white/[0.02] border-white/[0.06]'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] text-slate-500 font-bold uppercase">
                    TIER {tier.tierOrder}
                  </span>
                  <AurixBadge
                    variant={isSevere ? 'danger' : isModerate ? 'warning' : 'success'}
                    size="sm"
                  >
                    {tier.distortionRisk}
                  </AurixBadge>
                </div>

                <div className="text-white font-bold text-xs truncate mb-2">{tier.tierName}</div>

                <div className="space-y-1 text-[10px] border-t border-white/[0.04] pt-2">
                  <div className="flex justify-between">
                    <span className="text-slate-400">DEMAND VAR (σ²):</span>
                    <span className="text-slate-300">{tier.demandVariance.toFixed(1)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">ORDER VAR (σ²):</span>
                    <span className="text-slate-300">{tier.orderVariance.toFixed(1)}</span>
                  </div>
                  <div className="flex justify-between pt-1 border-t border-white/[0.04] items-center">
                    <span className="text-slate-400 flex items-center gap-1">
                      <Activity className="w-3 h-3 text-gold" /> BULLWHIP:
                    </span>
                    <span
                      className={`font-bold flex items-center ${
                        tier.bullwhipRatio > 1.3
                          ? 'text-[#FF6B6B]'
                          : tier.bullwhipRatio > 1.0
                          ? 'text-[#F3B33D]'
                          : 'text-[#3DDB91]'
                      }`}
                    >
                      {tier.bullwhipRatio.toFixed(2)}x
                      <ArrowUpRight className="w-3 h-3" />
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </AurixCard>
  );
};
