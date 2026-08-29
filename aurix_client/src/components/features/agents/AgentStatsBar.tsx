'use client';

import React from 'react';

import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { Bot, Cpu, Zap, ShieldCheck } from 'lucide-react';

export const AgentStatsBar: React.FC<{ summary?: any}> = ({ summary }) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 select-none font-mono">
      <AurixCard title="AUTONOMOUS AGENTS" badge={<AurixBadge variant="gold">ACTIVE ENGINES</AurixBadge>}>
        <div className="flex items-baseline justify-between mt-2">
          <span className="text-2xl font-bold text-white">0{summary.totalActiveAgents}</span>
          <Bot className="w-5 h-5 text-gold" />
        </div>
        <div className="text-[11px] text-slate-400 mt-1">Orchestrating Phase 16 tasks</div>
      </AurixCard>

      <AurixCard title="TASKS RUN TODAY" badge={<AurixBadge variant="info">THROUGHPUT</AurixBadge>}>
        <div className="flex items-baseline justify-between mt-2">
          <span className="text-2xl font-bold text-[#D4AF37]">{summary.tasksExecutedToday} Tasks</span>
          <Zap className="w-5 h-5 text-[#D4AF37]" />
        </div>
        <div className="text-[11px] text-slate-400 mt-1">{summary.autonomousInterventionsCount} automated interventions</div>
      </AurixCard>

      <AurixCard title="MEAN TOOL LATENCY" badge={<AurixBadge variant="success">EFFICIENCY</AurixBadge>}>
        <div className="flex items-baseline justify-between mt-2">
          <span className="text-2xl font-bold text-[#3DDB91]">{summary.meanToolLatencyMs} ms</span>
          <Cpu className="w-5 h-5 text-[#3DDB91]" />
        </div>
        <div className="text-[11px] text-slate-400 mt-1">Deterministic engine compute time</div>
      </AurixCard>

      <AurixCard title="GOVERNANCE CLEARANCE" badge={<AurixBadge variant="gold">PHASE 14</AurixBadge>}>
        <div className="flex items-baseline justify-between mt-2">
          <span className="text-2xl font-bold text-white">{summary.governanceClearanceRatePercent}%</span>
          <ShieldCheck className="w-5 h-5 text-gold" />
        </div>
        <div className="text-[11px] text-slate-400 mt-1">100% preflight gate compliance</div>
      </AurixCard>
    </div>
  );
};