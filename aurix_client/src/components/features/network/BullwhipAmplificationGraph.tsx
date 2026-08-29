'use client';

import React from 'react';
import { BullwhipTierMetric } from '@/types/network.types';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';


interface BullwhipAmplificationGraphProps {
  metrics: BullwhipTierMetric[];
}

export const BullwhipAmplificationGraph: React.FC<BullwhipAmplificationGraphProps> = ({ metrics }) => {
  return (
    <AurixCard
      title="BULLWHIP EFFECT & VARIANCE PROPAGATION"
      badge={<AurixBadge variant="warning">AMPLIFICATION RISK</AurixBadge>}
    >
      <div className="space-y-4 text-xs font-mono">
        <p className="text-slate-400 text-[11px] leading-relaxed">
          Order variance distortion accelerates upstream from Customer POS (1.0x baseline) to Tier-1 Suppliers (1.90x distortion).
        </p>

        <div className="space-y-3 pt-2">
          {metrics.map((tier) => {
            const isSevere = tier.distortionRisk === 'SEVERE';
            const isModerate = tier.distortionRisk === 'MODERATE';

            return (
              <div key={tier.tierName} className="space-y-1.5">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-white font-bold flex items-center gap-2">
                    <span className="text-slate-500 text-[10px]">Tier 0{tier.tierOrder}:</span>
                    {tier.tierName}
                  </span>
                  <div className="flex items-center gap-2">
                    <span className="text-slate-400 text-[10px]">Variance: {tier.orderVariance}</span>
                    <span className={`font-bold ${isSevere ? 'text-[#FF6B6B]' : isModerate ? 'text-gold' : 'text-[#3DDB91]'}`}>
                      {tier.bullwhipRatio.toFixed(2)}x
                    </span>
                  </div>
                </div>

                <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      isSevere
                        ? 'bg-gradient-to-r from-gold to-[#FF6B6B]'
                        : isModerate
                        ? 'bg-gradient-to-r from-[#B8912A] to-gold'
                        : 'bg-[#D4AF37]'
                    }`}
                    style={{ width: `${(tier.bullwhipRatio / 2.0) * 100}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </AurixCard>
  );
};