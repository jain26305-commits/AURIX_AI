'use client';

import React from 'react';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { AurixButton } from '@/components/ui/AurixButton';
import { Play } from 'lucide-react';

interface ScenarioBuilderSidebarProps {
  leadTimeDelta: number;
  onLeadTimeChange: (val: number) => void;
  serviceLevelTarget: number;
  onServiceLevelChange: (val: number) => void;
  demandSurge: number;
  onDemandSurgeChange: (val: number) => void;
  onRunSimulation: () => void;
  isSimulating: boolean;
}

export const ScenarioBuilderSidebar: React.FC<ScenarioBuilderSidebarProps> = ({
  leadTimeDelta,
  onLeadTimeChange,
  serviceLevelTarget,
  onServiceLevelChange,
  demandSurge,
  onDemandSurgeChange,
  onRunSimulation,
  isSimulating,
}) => {
  return (
    <AurixCard
      title="WHAT-IF PARAMETER STUDIO"
      badge={<AurixBadge variant="gold">INTERACTIVE</AurixBadge>}
    >
      <div className="space-y-6 text-xs font-mono">
        {/* Param 1: Lead Time Compression/Inflation */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-slate-300">LEAD-TIME SHIFT:</span>
            <span className={leadTimeDelta < 0 ? 'text-[#3DDB91] font-bold' : 'text-[#FF8585] font-bold'}>
              {leadTimeDelta > 0 ? `+${leadTimeDelta}` : leadTimeDelta} Days
            </span>
          </div>
          <input
            type="range"
            min="-14"
            max="14"
            step="1"
            value={leadTimeDelta}
            onChange={(e) => onLeadTimeChange(Number(e.target.value))}
            className="w-full h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer accent-gold focus:outline-none"
          />
          <div className="flex justify-between text-[9px] text-slate-500">
            <span>-14d (Expedite)</span>
            <span>0d (Baseline)</span>
            <span>+14d (Delay)</span>
          </div>
        </div>

        {/* Param 2: Target Service Level */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-slate-300">SERVICE TARGET:</span>
            <span className="text-gold font-bold">{serviceLevelTarget}%</span>
          </div>
          <input
            type="range"
            min="90"
            max="99"
            step="1"
            value={serviceLevelTarget}
            onChange={(e) => onServiceLevelChange(Number(e.target.value))}
            className="w-full h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer accent-gold focus:outline-none"
          />
          <div className="flex justify-between text-[9px] text-slate-500">
            <span>90%</span>
            <span>95% (Default)</span>
            <span>99%</span>
          </div>
        </div>

        {/* Param 3: Demand Surge Multiplier */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-slate-300">SEASONAL DEMAND SURGE:</span>
            <span className="text-[#D4AF37] font-bold">+{demandSurge}%</span>
          </div>
          <input
            type="range"
            min="0"
            max="50"
            step="5"
            value={demandSurge}
            onChange={(e) => onDemandSurgeChange(Number(e.target.value))}
            className="w-full h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer accent-[#D4AF37] focus:outline-none"
          />
          <div className="flex justify-between text-[9px] text-slate-500">
            <span>+0%</span>
            <span>+25% (Promo)</span>
            <span>+50% (Black Swan)</span>
          </div>
        </div>

        {/* Action Button */}
        <div className="pt-2">
          <AurixButton
            variant="gold"
            size="md"
            className="w-full"
            onClick={onRunSimulation}
            loading={isSimulating}
          >
            <Play className="w-4 h-4 mr-1.5 fill-current" />
            <span>RUN SIMULATION</span>
          </AurixButton>
        </div>
      </div>
    </AurixCard>
  );
};