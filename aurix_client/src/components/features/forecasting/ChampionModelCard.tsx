'use client';

import React from 'react';
import { ChampionModelMetadata } from '@/types/forecast.types';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { AurixButton } from '@/components/ui/AurixButton';
import { Cpu, HelpCircle } from 'lucide-react';

interface ChampionModelCardProps {
  metadata: ChampionModelMetadata;
  onOpenTransparency: () => void;
}

export const ChampionModelCard: React.FC<ChampionModelCardProps> = ({ metadata, onOpenTransparency }) => {
  return (
    <AurixCard
      title="CHAMPION MODEL CERTIFICATION"
      badge={<AurixBadge variant="gold" pulse>CHAMPION</AurixBadge>}
      headerAction={
        <AurixButton variant="ghost" size="sm" onClick={onOpenTransparency}>
          <HelpCircle className="w-3.5 h-3.5 mr-1" />
          <span>WHY THIS MODEL?</span>
        </AurixButton>
      }
    >
      <div className="space-y-4">
        <div className="flex items-center justify-between pt-1">
          <div>
            <span className="text-xs font-mono text-slate-500 uppercase tracking-widest block">ALGORITHM</span>
            <span className="text-xl font-bold font-mono text-white tracking-wide flex items-center gap-2 mt-0.5">
              <Cpu className="w-5 h-5 text-gold" />
              {metadata.modelFamily}
            </span>
          </div>

          <div className="text-right">
            <span className="text-xs font-mono text-slate-500 uppercase tracking-widest block">CONFIDENCE</span>
            <span className="text-xl font-bold font-mono text-[#3DDB91] mt-0.5">
              {metadata.confidenceScorePercent}%
            </span>
          </div>
        </div>

        <p className="text-xs font-mono text-slate-300 leading-relaxed bg-white/[0.02] p-3 rounded-lg border border-white/[0.04]">
          {metadata.rationale}
        </p>

        <div className="grid grid-cols-3 gap-3 pt-2 border-t border-white/[0.06] text-xs font-mono">
          <div>
            <span className="text-slate-500 block text-[10px]">OUT-OF-SAMPLE ERROR</span>
            <span className="text-white font-bold">{metadata.accuracyWape}% WAPE</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px]">HORIZON DEMAND</span>
            <span className="text-gold font-bold">{metadata.horizonUnitsTotal} pcs</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px]">TRAINING HISTORY</span>
            <span className="text-white font-bold">{metadata.historicalMonthsTrained} Months</span>
          </div>
        </div>
      </div>
    </AurixCard>
  );
};