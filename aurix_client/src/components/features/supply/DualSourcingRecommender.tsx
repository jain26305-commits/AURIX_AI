'use client';

import React from 'react';
import { DualSourcingRecommendation } from '@/types/supply.types';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { AurixButton } from '@/components/ui/AurixButton';
import { GitFork, CheckCircle, Clock } from 'lucide-react';

interface DualSourcingRecommenderProps {
  recommendations?: DualSourcingRecommendation[];
}

export const DualSourcingRecommender: React.FC<DualSourcingRecommenderProps> = ({
  recommendations = [],
}) => {
  if (recommendations.length === 0) {
    return (
      <AurixCard
        title="DUAL-SOURCING & ALTERNATIVE VENDOR MITIGATION"
        badge={<AurixBadge variant="success">SUFFICIENT DIVERSIFICATION</AurixBadge>}
      >
        <div className="h-24 flex items-center justify-center font-mono text-xs text-slate-500">
          NO SINGLE-SOURCE CONCENTRATION BREACHES DETECTED
        </div>
      </AurixCard>
    );
  }

  return (
    <AurixCard
      title="DUAL-SOURCING & ALTERNATIVE VENDOR MITIGATION"
      badge={<AurixBadge variant="warning">BACKEND SELECTOR ACTIVE</AurixBadge>}
    >
      <div className="space-y-4 pt-2 font-mono text-xs">
        {recommendations.map((rec) => (
          <div
            key={rec.targetSkuId}
            className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06] space-y-3"
          >
            {/* Context Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-white/[0.04]">
              <div>
                <span className="text-white font-bold flex items-center gap-1.5">
                  <GitFork className="w-3.5 h-3.5 text-gold" />
                  {rec.targetSkuId}
                </span>
                <span className="text-[10px] text-slate-500 block">
                  Primary Vendor: {rec.currentPrimarySupplierId} • Annualized Exposure: ₹{(rec.annualizedSpendExposureINR / 100000).toFixed(2)}L
                </span>
              </div>
              <AurixBadge variant="danger" size="sm">CONCENTRATION RISK</AurixBadge>
            </div>

            {/* Candidate List */}
            <div className="space-y-2">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">
                EVALUATED ALTERNATIVE CANDIDATES (BACKEND ENGINE)
              </span>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {rec.recommendedCandidates.map((cand) => (
                  <div
                    key={cand.supplierId}
                    className="p-3 rounded-lg bg-black/40 border border-white/[0.04] flex flex-col justify-between space-y-2"
                  >
                    <div>
                      <div className="flex items-center justify-between">
                        <span className="text-white font-bold truncate">{cand.supplierName}</span>
                        <span className="text-gold font-bold">{cand.matchScorePercent}% Match</span>
                      </div>
                      <span className="text-[10px] text-slate-500 block mt-0.5">
                        ID: {cand.supplierId} • Est. Lead Time: {cand.estimatedLeadTimeDays}d • ₹{cand.unitCostINR}/unit
                      </span>
                    </div>

                    <div className="flex items-center justify-between pt-2 border-t border-white/[0.04]">
                      <span className="text-[10px] text-slate-400 flex items-center gap-1">
                        {cand.qualificationStatus === 'QUALIFIED' ? (
                          <CheckCircle className="w-3 h-3 text-[#3DDB91]" />
                        ) : (
                          <Clock className="w-3 h-3 text-[#F3B33D]" />
                        )}
                        {cand.qualificationStatus}
                      </span>
                      <AurixButton variant="secondary" size="sm">
                        ALLOCATE SPLIT
                      </AurixButton>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </AurixCard>
  );
};
