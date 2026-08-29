'use client';

import React from 'react';
import { ModelRegistryEntry } from '@/types/admin.types';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { AurixButton } from '@/components/ui/AurixButton';
import { RefreshCw, Trophy } from 'lucide-react';

interface ModelRegistryTableProps {
  models: ModelRegistryEntry[];
  retrainingId: string | null;
  onRetrain: (id: string) => void;
}

export const ModelRegistryTable: React.FC<ModelRegistryTableProps> = ({
  models,
  retrainingId,
  onRetrain,
}) => {
  return (
    <div className="w-full aurix-card-glass rounded-xl p-6 border border-white/[0.08] select-none font-mono">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-white/[0.08] text-slate-500 text-[10px] uppercase tracking-wider">
              <th className="pb-3 pl-2">Model & Version</th>
              <th className="pb-3">Algorithm Family</th>
              <th className="pb-3">Target Domain</th>
              <th className="pb-3">WAPE Error</th>
              <th className="pb-3">Drift Status</th>
              <th className="pb-3">Environment</th>
              <th className="pb-3 text-right pr-2">MLOps Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.04]">
            {models.map((m) => {
              const isRetraining = retrainingId === m.modelId;

              return (
                <tr key={m.modelId} className="hover:bg-white/[0.02] transition-colors">
                  <td className="py-3.5 pl-2">
                    <div className="flex items-center gap-2">
                      {m.isChampion && <Trophy className="w-3.5 h-3.5 text-gold shrink-0" />}
                      <div>
                        <span className="text-white font-bold text-xs block">{m.modelName}</span>
                        <span className="text-slate-500 text-[10px]">{m.modelId} • {m.version}</span>
                      </div>
                    </div>
                  </td>

                  <td className="py-3.5">
                    <AurixBadge variant="gold">{m.algorithmFamily}</AurixBadge>
                  </td>

                  <td className="py-3.5 text-slate-300">{m.targetDomain.replace('_', ' ')}</td>

                  <td className="py-3.5">
                    <span className="text-white font-bold">{m.wapePercent}%</span>
                    <span className="text-slate-500 text-[10px] block">RMSE: {m.rmse}</span>
                  </td>

                  <td className="py-3.5">
                    <AurixBadge
                      variant={m.driftStatus === 'STABLE' ? 'success' : m.driftStatus === 'MODERATE_DRIFT' ? 'warning' : 'danger'}
                    >
                      {m.driftStatus.replace('_', ' ')}
                    </AurixBadge>
                  </td>

                  <td className="py-3.5">
                    <span className="text-[#D4AF37] font-bold text-[11px]">{m.deployedEnvironment}</span>
                  </td>

                  <td className="py-3.5 text-right pr-2">
                    <AurixButton
                      variant="secondary"
                      size="sm"
                      onClick={() => onRetrain(m.modelId)}
                      loading={isRetraining}
                    >
                      <RefreshCw className="w-3 h-3 mr-1" />
                      <span>RETRAIN</span>
                    </AurixButton>
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