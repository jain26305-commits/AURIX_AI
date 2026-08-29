'use client';

import React from 'react';
import { AlertTriangle, TrendingUp, Sparkles, ArrowUpRight } from 'lucide-react';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';

export interface DomainSignal {
  id: string;
  title: string;
  impact: string;
  type: 'risk' | 'opportunity' | 'alert';
  severity?: 'critical' | 'warning' | 'info';
  actionPrompt?: string;
  onAction?: () => void;
}

export interface DomainSignalsOverviewProps {
  signals?: DomainSignal[];
  title?: string;
}

export const DomainSignalsOverview: React.FC<DomainSignalsOverviewProps> = ({
  signals = [],
  title = 'DOMAIN INTELLIGENCE SIGNALS',
}) => {
  if (signals.length === 0) return null;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Sparkles className="w-3.5 h-3.5 text-[#D4AF37]" />
        <h2 className="text-xs font-mono font-bold tracking-[0.2em] text-white uppercase">
          {title}
        </h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {signals.map((sig) => {
          const isRisk = sig.type === 'risk';
          const isOpp = sig.type === 'opportunity';

          return (
            <AurixCard
              key={sig.id}
              variant="interactive"
              className="p-4 space-y-3 border-white/[0.06] hover:border-[#D4AF37]/40"
              onClick={sig.onAction}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2 min-w-0">
                  {isRisk ? (
                    <AlertTriangle className="w-4 h-4 text-[#FF6B6B] shrink-0" />
                  ) : isOpp ? (
                    <TrendingUp className="w-4 h-4 text-[#3DDB91] shrink-0" />
                  ) : (
                    <Sparkles className="w-4 h-4 text-[#D4AF37] shrink-0" />
                  )}
                  <span className="text-xs font-mono font-bold text-white uppercase tracking-wider truncate">
                    {sig.title}
                  </span>
                </div>
                <AurixBadge
                  variant={isRisk ? 'danger' : isOpp ? 'success' : 'gold'}
                  size="sm"
                >
                  {sig.type.toUpperCase()}
                </AurixBadge>
              </div>

              <div className="pt-2 border-t border-white/[0.04] flex items-center justify-between text-xs font-mono">
                <span className="text-[10px] text-slate-500 uppercase tracking-wider">PROJECTED IMPACT</span>
                <span className="font-bold text-white tracking-wider">{sig.impact}</span>
              </div>

              {sig.actionPrompt && (
                <div className="flex items-center justify-between text-[10px] font-mono text-[#D4AF37] group-hover:underline pt-1">
                  <span>{sig.actionPrompt}</span>
                  <ArrowUpRight className="w-3 h-3" />
                </div>
              )}
            </AurixCard>
          );
        })}
      </div>
    </div>
  );
};
