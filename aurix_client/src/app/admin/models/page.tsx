'use client';

import React from 'react';
import { ModelRegistryTable } from '@/components/features/admin/ModelRegistryTable';
import { useAdminModels } from '@/hooks/useAdminModels';
import { AurixButton } from '@/components/ui/AurixButton';
import { RotateCw } from 'lucide-react';
import { useWorkspaceHeader } from '@/context/WorkspaceHeaderContext';

export default function ModelsPage() {
  useWorkspaceHeader({ activeWorkspaceTitle: "MLOps Model Registry" });
  const { models, loading, retrainingId, handleRetrain, reload } = useAdminModels();

  if (loading) {
    return (
      <>
        <div className="py-24 flex flex-col items-center justify-center text-center space-y-4 font-mono">
          <div className="w-8 h-8 rounded-full border-2 border-gold border-t-transparent animate-spin" />
          <p className="text-xs text-slate-400 tracking-widest uppercase">AUDITING ML MODEL REGISTRY & DRIFT...</p>
        </div>
      </>
    );
  }

  return (
    <>
      <div className="space-y-8 animate-pure-fade font-mono">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2 py-0.5 rounded bg-gold/10 border border-gold/30 text-gold text-[10px] font-bold tracking-widest uppercase">
                MLOPS REGISTRY
              </span>
              <span className="text-slate-500 text-xs">• CHAMPION / CHALLENGER</span>
            </div>
            <h1 className="text-xl font-bold text-white tracking-wide">MODEL REGISTRY & PERFORMANCE MONITOR</h1>
            <p className="text-xs text-slate-400 mt-0.5">
              Track algorithm versions, WAPE backtest benchmarks, data drift indicators, and retraining pipelines.
            </p>
          </div>

          <AurixButton variant="secondary" size="sm" onClick={reload}>
            <RotateCw className="w-3.5 h-3.5 mr-1.5" /> RE-EVALUATE
          </AurixButton>
        </div>

        <ModelRegistryTable
          models={models}
          retrainingId={retrainingId}
          onRetrain={handleRetrain}
        />
      </div>
    </>
  );
}