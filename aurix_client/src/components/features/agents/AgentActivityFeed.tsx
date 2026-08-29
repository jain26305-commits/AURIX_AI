'use client';

import React from 'react';
import { AgentTask } from '@/types/agent.types';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { Bot, Cpu, ChevronRight } from 'lucide-react';

interface AgentActivityFeedProps {
  tasks?: any[];
  selectedTask: AgentTask | null;
  onSelectTask: (task: AgentTask) => void;
}

export const AgentActivityFeed: React.FC<AgentActivityFeedProps> = ({
  tasks,
  selectedTask,
  onSelectTask,
}) => {
  return (
    <div className="w-full aurix-card-glass rounded-xl p-6 border border-white/[0.08] select-none font-mono space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
        <h3 className="text-sm font-bold text-white tracking-wide flex items-center gap-2">
          <Bot className="w-4 h-4 text-gold" />
          AUTONOMOUS AGENT ORCHESTRATION TIMELINE (PHASE 16)
        </h3>
        <span className="text-slate-500 text-xs">Deterministic Tool Invocations</span>
      </div>

      <div className="space-y-3">
        {(tasks || []).map((t) => {
          const isSelected = selectedTask?.taskId === t.taskId;

          return (
            <div
              key={t.taskId}
              onClick={() => onSelectTask(t)}
              className={`p-4 rounded-xl border cursor-pointer transition-all space-y-2.5 ${
                isSelected
                  ? 'bg-gold/[0.06] border-gold/40 shadow-[0_0_15px_rgba(212,175,55,0.1)]'
                  : 'bg-white/[0.02] border-white/[0.06] hover:border-white/20'
              }`}
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-slate-500 font-bold">{t.taskId}</span>
                  <AurixBadge variant="gold">{t.agentRole.replace('_', ' ')}</AurixBadge>
                  <span className="text-white font-bold text-xs">{t.agentName}</span>
                </div>

                <div className="flex items-center gap-3">
                  <span className="text-slate-500 text-[10px]">{t.durationMs}ms</span>
                  <AurixBadge variant="success">SUCCESS</AurixBadge>
                </div>
              </div>

              <div className="text-slate-300 text-xs leading-relaxed">
                <span className="text-gold font-bold">TRIGGER: </span>
                {t.triggerEvent}
              </div>

              <p className="text-slate-400 text-[11px] leading-relaxed">
                {t.evidenceSummary}
              </p>

              <div className="pt-2 border-t border-white/[0.04] flex items-center justify-between text-[10px]">
                <div className="flex items-center gap-1.5 text-slate-400">
                  <Cpu className="w-3.5 h-3.5 text-[#D4AF37]" />
                  <span>TOOLS INVOKED: <strong className="text-white">{(t.toolsUsed || []).length} Engines</strong></span>
                </div>

                <div className="flex items-center gap-1 text-gold hover:underline font-bold">
                  <span>INSPECT TRACE</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};