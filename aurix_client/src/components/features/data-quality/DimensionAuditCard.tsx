'use client';

import React from 'react';
import { QualityDimensionScore } from '@/types/quality.types';
import { Shield, AlertTriangle, CheckCircle2, XCircle } from 'lucide-react';

interface DimensionAuditCardProps {
  dimensions: QualityDimensionScore[];
}

export const DimensionAuditCard: React.FC<DimensionAuditCardProps> = ({ dimensions }) => {
  return (
    <div className="w-full aurix-card-glass rounded-xl p-6 border border-white/[0.08]">
      <div className="flex items-center justify-between pb-4 mb-4 border-b border-white/[0.06]">
        <div>
          <h3 className="text-sm font-semibold text-white tracking-wide flex items-center gap-2">
            <Shield className="w-4 h-4 text-gold" />
            7-DIMENSION INTEGRITY AUDIT
          </h3>
          <p className="text-[11px] font-mono text-slate-400 mt-0.5">
            Granular evaluation of temporal continuity, outlier density, and schema completeness.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {dimensions.map((dim) => {
          const isOptimal = dim.status === 'optimal';
          const isAcceptable = dim.status === 'acceptable';

          return (
            <div
              key={dim.key}
              className={`p-4 rounded-xl border transition-all duration-200 flex flex-col justify-between ${
                isOptimal
                  ? 'bg-white/[0.02] border-white/[0.06] hover:border-white/15'
                  : isAcceptable
                  ? 'bg-[#F3B33D]/5 border-[#F3B33D]/25'
                  : 'bg-[#FF6B6B]/5 border-[#FF6B6B]/25'
              }`}
            >
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-white tracking-wide">{dim.name}</span>
                  <div className="flex items-center gap-1.5 font-mono text-xs font-bold">
                    {isOptimal ? (
                      <span className="text-[#3DDB91] flex items-center gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5" /> {dim.score}%
                      </span>
                    ) : isAcceptable ? (
                      <span className="text-[#F3B33D] flex items-center gap-1">
                        <AlertTriangle className="w-3.5 h-3.5" /> {dim.score}%
                      </span>
                    ) : (
                      <span className="text-[#FF6B6B] flex items-center gap-1">
                        <XCircle className="w-3.5 h-3.5" /> {dim.score}%
                      </span>
                    )}
                  </div>
                </div>

                <p className="text-[11px] font-mono text-slate-400 mt-2 leading-relaxed">
                  {dim.description}
                </p>
              </div>

              {/* Metric Bar */}
              <div className="mt-4 pt-3 border-t border-white/[0.04] flex items-center justify-between text-[10px] font-mono text-slate-500">
                <span>IMPACTED:</span>
                <span className="text-slate-300 font-medium">
                  {dim.affectedRecords} / {dim.totalRecords} rows
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};