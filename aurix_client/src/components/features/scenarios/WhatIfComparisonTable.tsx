'use client';

import React from 'react';
import { ScenarioOutcomeDelta } from '@/types/scenario.types';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { Sparkles } from 'lucide-react';

interface WhatIfComparisonTableProps {
  baseScenario: ScenarioOutcomeDelta;
  branches?: any[];
  activeScenarioId: string;
  onSelectScenario: (id: string) => void;
}

export const WhatIfComparisonTable: React.FC<WhatIfComparisonTableProps> = ({
  baseScenario,
  branches,
  activeScenarioId,
  onSelectScenario,
}) => {
  const allScenarios = [baseScenario, ...(branches || [])];

  return (
    <div className="w-full aurix-card-glass rounded-xl p-6 border border-white/[0.08]">
      <div className="flex items-center justify-between pb-4 mb-4 border-b border-white/[0.06]">
        <div>
          <h3 className="text-sm font-semibold text-white tracking-wide flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-gold" />
            SCENARIO OUTCOME COMPARISON MATRIX
          </h3>
          <p className="text-[11px] font-mono text-slate-400 mt-0.5">
            Multi-branch evaluation across service levels, capital allocation, and net financial ROI.
          </p>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs font-mono">
          <thead>
            <tr className="border-b border-white/[0.08] text-slate-500 text-[10px] uppercase tracking-wider">
              <th className="pb-3 pl-2">Simulation Branch</th>
              <th className="pb-3">Service Level</th>
              <th className="pb-3">Working Capital</th>
              <th className="pb-3">Stockout Risk</th>
              <th className="pb-3">Expedite Premium</th>
              <th className="pb-3">Net ROI Impact</th>
              <th className="pb-3 text-right pr-2">Decision Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.04]">
            {allScenarios.map((scen) => {
              const isSelected = scen.scenarioId === activeScenarioId;

              return (
                <tr
                  key={scen.scenarioId}
                  onClick={() => onSelectScenario(scen.scenarioId)}
                  className={`cursor-pointer transition-colors ${
                    isSelected ? 'bg-gold/[0.06]' : 'hover:bg-white/[0.02]'
                  }`}
                >
                  <td className="py-3 pl-2">
                    <div className="flex flex-col">
                      <span className={`font-bold ${isSelected ? 'text-gold' : 'text-white'}`}>
                        {scen.name}
                      </span>
                      <span className="text-[10px] text-slate-500">{scen.branchType}</span>
                    </div>
                  </td>

                  <td className="py-3">
                    <span className="font-bold text-white">{scen.projectedServiceLevelPercent}%</span>
                    {scen.serviceLevelDeltaPercent !== 0 && (
                      <span
                        className={`text-[10px] ml-1.5 font-bold ${
                          scen.serviceLevelDeltaPercent > 0 ? 'text-[#3DDB91]' : 'text-[#FF6B6B]'
                        }`}
                      >
                        ({scen.serviceLevelDeltaPercent > 0 ? `+${scen.serviceLevelDeltaPercent}` : scen.serviceLevelDeltaPercent}%)
                      </span>
                    )}
                  </td>

                  <td className="py-3 text-slate-300">
                    ₹{(scen.totalWorkingCapitalINR / 100000).toFixed(2)}L
                  </td>

                  <td className="py-3 text-slate-400">
                    ₹{(scen.stockoutRiskExposureINR / 100000).toFixed(2)}L
                  </td>

                  <td className="py-3 text-slate-400">
                    ₹{(scen.expediteCostINR / 100000).toFixed(2)}L
                  </td>

                  <td className="py-3 font-bold">
                    <span className={scen.netFinancialImpactINR >= 0 ? 'text-[#3DDB91]' : 'text-[#FF6B6B]'}>
                      {scen.netFinancialImpactINR >= 0 ? `+₹${(scen.netFinancialImpactINR / 100000).toFixed(2)}L` : `-₹${(Math.abs(scen.netFinancialImpactINR) / 100000).toFixed(2)}L`}
                    </span>
                  </td>

                  <td className="py-3 text-right pr-2">
                    {scen.isRecommended ? (
                      <AurixBadge variant="gold" pulse>RECOMMENDED</AurixBadge>
                    ) : (
                      <span className="text-slate-500 text-[10px]">CANDIDATE</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};