'use client';

import React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { UrgentSignalItem } from '@/types/control-tower.types';
import { DecisionCard } from '@/components/visualizations/DecisionCard';
import { Zap, ArrowRight } from 'lucide-react';

interface TopSignalsActionFeedProps {
  signals: UrgentSignalItem[];
}

export const TopSignalsActionFeed: React.FC<TopSignalsActionFeedProps> = ({ signals }) => {
  const router = useRouter();

  return (
    <div className="w-full aurix-card-glass rounded-xl p-6 border border-white/[0.08] select-none space-y-4">
      <div className="flex items-center justify-between pb-4 border-b border-white/[0.06]">
        <div>
          <h3 className="text-sm font-semibold text-white tracking-wide flex items-center gap-2 font-mono">
            <Zap className="w-4 h-4 text-[#D4AF37]" />
            EXECUTIVE PRESCRIPTIVE ACTION QUEUE
          </h3>
          <p className="text-[11px] font-mono text-slate-400 mt-0.5">
            Ranked prescriptive decisions evaluated across Expected Value (EV), confidence intervals, and preflight security.
          </p>
        </div>

        <Link
          href="/decisions?subdomain=feed"
          className="text-xs font-mono text-[#D4AF37] hover:text-white flex items-center gap-1 transition-colors"
        >
          <span>VIEW DECISION FEED</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {signals.map((sig) => {
          const riskLevel = sig.severity === 'CRITICAL' ? 'HIGH' : sig.severity === 'HIGH' ? 'MEDIUM' : 'LOW';
          const confidenceScore = sig.severity === 'CRITICAL' ? 96 : sig.severity === 'HIGH' ? 88 : 82;

          return (
            <DecisionCard
              key={sig.id}
              id={sig.id}
              title={sig.title}
              domain={sig.category || 'OPERATIONS'}
              expectedValue={`+₹${(sig.exposureINR / 100000).toFixed(2)}L`}
              confidenceScore={confidenceScore}
              riskLevel={riskLevel}
              preflightStatus="PASSED"
              rationale={sig.prescriptiveSummary}
              onExecute={() => {
                router.push(sig.recommendationRoute || '/decisions?subdomain=preflight');
              }}
              onSimulate={() => {
                router.push('/scenarios?subdomain=simulator');
              }}
            />
          );
        })}
      </div>
    </div>
  );
};
