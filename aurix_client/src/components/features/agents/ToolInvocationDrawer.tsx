'use client';

import React from 'react';
import { AgentTask } from '@/types/agent.types';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { X, Cpu, CheckCircle2, Terminal } from 'lucide-react';

interface ToolInvocationDrawerProps {
  task: AgentTask | null;
  isOpen: boolean;
  onClose: () => void;
}

export const ToolInvocationDrawer: React.FC<ToolInvocationDrawerProps> = ({
  task,
  isOpen,
  onClose,
}) => {
  if (!isOpen || !task) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm animate-pure-fade select-none font-mono">
      <div className="w-full max-w-xl bg-[#0C0E12] border-l border-white/10 h-full p-6 overflow-y-auto space-y-6">
        <div className="flex items-center justify-between pb-4 border-b border-white/10">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Cpu className="w-5 h-5 text-gold" />
              TOOL INVOCATION & EVIDENCE TRACE
            </h3>
            <span className="text-xs text-slate-400">{task.taskId} • {task.agentName}</span>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg bg-white/[0.05] hover:bg-white/10 text-slate-400 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="space-y-4">
          <span className="text-[10px] text-gold uppercase tracking-widest font-bold block">
            DETERMINISTIC TOOLS EXECUTED ({(task?.toolsUsed || []).length})
          </span>

          <div className="space-y-3">
            {(task?.toolsUsed || []).map((tool: any) => (
              <div
                key={tool.invocationId}
                className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06] space-y-2.5 text-xs"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-[#3DDB91]" />
                    <span className="text-white font-bold text-xs">{tool.toolName}</span>
                  </div>
                  <AurixBadge variant="info">{tool.executionLatencyMs} ms</AurixBadge>
                </div>

                <div className="p-2.5 rounded-lg bg-black/40 border border-white/5 space-y-1">
                  <span className="text-[9px] text-slate-500 uppercase font-bold flex items-center gap-1">
                    <Terminal className="w-3 h-3 text-gold" /> PARAMETERS
                  </span>
                  <pre className="text-[10px] text-slate-300 overflow-x-auto">
                    {JSON.stringify(tool.inputParameters, null, 2)}
                  </pre>
                </div>

                <div className="p-2.5 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                  <span className="text-[9px] text-slate-500 uppercase font-bold block">OUTPUT SUMMARY</span>
                  <p className="text-slate-300 text-[11px] mt-0.5 leading-relaxed">{tool.outputSummary}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};