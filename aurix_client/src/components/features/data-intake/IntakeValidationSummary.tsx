'use client';

import React from 'react';
import { ValidationIssue } from '@/types/data-intake.types';
import { ShieldCheck, AlertOctagon, Info, ArrowRight } from 'lucide-react';
import { AurixButton } from '@/components/ui/AurixButton';

interface IntakeValidationSummaryProps {
  issues: ValidationIssue[];
  isReady: boolean;
  onCommit: () => void;
  isSubmitting?: boolean;
}

export const IntakeValidationSummary: React.FC<IntakeValidationSummaryProps> = ({
  issues,
  isReady,
  onCommit,
  isSubmitting = false,
}) => {
  const isCriticalOrError = (sev: string) => {
    const s = (sev || '').toLowerCase();
    return s === 'critical' || s === 'error';
  };

  const isWarning = (sev: string) => {
    const s = (sev || '').toLowerCase();
    return s === 'warning';
  };

  const hasCritical = issues.some((i) => isCriticalOrError(i.severity));

  return (
    <div className="w-full aurix-card-glass rounded-xl p-6 border border-white/[0.08] space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          {hasCritical ? (
            <AlertOctagon className="w-5 h-5 text-[#FF6B6B]" />
          ) : (
            <ShieldCheck className="w-5 h-5 text-[#3DDB91]" />
          )}
          <h3 className="text-sm font-semibold text-white tracking-wide">
            {hasCritical ? 'INGESTION BLOCKED: CRITICAL SCHEMA ISSUES' : 'SCHEMA INTEGRITY VALIDATED'}
          </h3>
        </div>

        <AurixButton
          variant={hasCritical ? 'secondary' : 'gold'}
          size="md"
          disabled={!isReady || hasCritical}
          loading={isSubmitting}
          onClick={onCommit}
        >
          <span>PROCEED TO DATA QUALITY</span>
          <ArrowRight className="w-4 h-4 ml-2" />
        </AurixButton>
      </div>

      {issues.length > 0 && (
        <div className="space-y-2 pt-2">
          {issues.map((issue, idx) => (
            <div
              key={idx}
              className={`p-3 rounded-lg border text-xs font-mono flex items-start gap-3 ${
                isCriticalOrError(issue.severity)
                  ? 'bg-[#FF6B6B]/10 border-[#FF6B6B]/30 text-[#FF8585]'
                  : isWarning(issue.severity)
                  ? 'bg-[#F3B33D]/10 border-[#F3B33D]/30 text-[#F3B33D]'
                  : 'bg-white/[0.03] border-white/[0.08] text-slate-300'
              }`}
            >
              <Info className="w-4 h-4 shrink-0 mt-0.5" />
              <div>
                <div className="font-semibold">{issue.message}</div>
                {issue.remediationSuggestion && (
                  <div className="text-[11px] text-slate-400 mt-0.5">{issue.remediationSuggestion}</div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};