'use client';

import React from 'react';
import { PipelineStage, IntakeStage } from '@/types/data-intake.types';
import { CheckCircle2, AlertCircle, Loader2, FileCheck, Database, Cpu, ShieldCheck } from 'lucide-react';

interface UploadPipelineStatusProps {
  stage: PipelineStage | IntakeStage;
  progressPercent: number;
  errorMessage?: string;
}

interface StepConfig {
  id: string;
  label: string;
  description: string;
  icon: React.ElementType;
  activeStages: (PipelineStage | IntakeStage)[];
  completionStages: (PipelineStage | IntakeStage)[];
}

const STEPS: StepConfig[] = [
  {
    id: 'ingest',
    label: 'File Ingest',
    description: 'Receiving file & validating integrity',
    icon: FileCheck,
    activeStages: ['file_received', 'uploading'],
    completionStages: ['understanding_data', 'mapping_structure', 'validating', 'ready', 'parsing', 'transforming', 'completed'],
  },
  {
    id: 'profile',
    label: 'Data Profiling',
    description: 'Analyzing row structure & distributions',
    icon: Cpu,
    activeStages: ['understanding_data', 'parsing'],
    completionStages: ['mapping_structure', 'validating', 'ready', 'transforming', 'completed'],
  },
  {
    id: 'mapping',
    label: 'Schema Mapping',
    description: 'Resolving canonical column synonyms',
    icon: Database,
    activeStages: ['mapping_structure', 'transforming'],
    completionStages: ['validating', 'ready', 'completed'],
  },
  {
    id: 'validation',
    label: 'Quality Gates',
    description: 'Checking mandatory domain rules',
    icon: ShieldCheck,
    activeStages: ['validating'],
    completionStages: ['ready', 'completed'],
  },
];

export const UploadPipelineStatus: React.FC<UploadPipelineStatusProps> = ({
  stage,
  progressPercent,
  errorMessage,
}) => {
  const isError = stage === 'error' || stage === 'failed';
  const isCompleted = stage === 'ready' || stage === 'completed';

  return (
    <div className="w-full aurix-card-glass rounded-xl p-6 border border-white/[0.08] space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-white tracking-wide">
            {isError
              ? 'INGESTION FAILED'
              : isCompleted
              ? 'INGESTION PIPELINE COMPLETE'
              : 'PROCESSING INGESTION PIPELINE'}
          </h3>
          <p className="text-xs font-mono text-slate-400 mt-0.5">
            {errorMessage || 'Executing deterministic data quality and schema discovery engines.'}
          </p>
        </div>
        <span className="text-xs font-mono font-bold text-gold px-2.5 py-1 rounded bg-gold/10 border border-gold/20">
          {progressPercent}%
        </span>
      </div>

      {/* Progress Bar */}
      <div className="w-full h-1.5 bg-white/[0.05] rounded-full overflow-hidden">
        <div
          className={`h-full transition-all duration-300 ease-out ${
            isError ? 'bg-[#FF6B6B]' : isCompleted ? 'bg-[#3DDB91]' : 'bg-gold'
          }`}
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {/* Pipeline Steps Breakdown */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {STEPS.map((step) => {
          const Icon = step.icon;
          const isCurrent = step.activeStages.includes(stage);
          const isDone = step.completionStages.includes(stage);

          return (
            <div
              key={step.id}
              className={`p-3.5 rounded-lg border text-xs font-mono transition-colors ${
                isCurrent
                  ? 'bg-gold/10 border-gold/30 text-white'
                  : isDone
                  ? 'bg-white/[0.03] border-[#3DDB91]/30 text-slate-200'
                  : 'bg-white/[0.01] border-white/[0.05] text-slate-500'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <Icon className={`w-4 h-4 ${isCurrent ? 'text-gold' : isDone ? 'text-[#3DDB91]' : 'text-slate-600'}`} />
                  <span className="font-semibold">{step.label}</span>
                </div>
                {isCurrent && <Loader2 className="w-3.5 h-3.5 text-gold animate-spin" />}
                {isDone && <CheckCircle2 className="w-3.5 h-3.5 text-[#3DDB91]" />}
              </div>
              <p className="text-[10px] text-slate-400 line-clamp-2">{step.description}</p>
            </div>
          );
        })}
      </div>

      {isError && errorMessage && (
        <div className="p-3 rounded-lg bg-[#FF6B6B]/10 border border-[#FF6B6B]/30 flex items-start gap-2.5 text-xs text-[#FF8585] font-mono">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>{errorMessage}</span>
        </div>
      )}
    </div>
  );
};