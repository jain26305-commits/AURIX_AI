'use client';

import React from 'react';
import { Phase14ActionItem } from '@/types/action.types';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { AurixButton } from '@/components/ui/AurixButton';
import { ShieldCheck, FileKey, Play, CheckCircle2, AlertTriangle } from 'lucide-react';
import { formatINR } from '@/lib/formatters';

interface ActionQueueTableProps {
  actions: Phase14ActionItem[];
  onOpenPreflight: (action: Phase14ActionItem) => void;
  onOpenToken: (action: Phase14ActionItem) => void;
  onExecute: (id: string) => void;
}

export const ActionQueueTable: React.FC<ActionQueueTableProps> = ({
  actions,
  onOpenPreflight,
  onOpenToken,
  onExecute,
}) => {
  return (
    <div className="w-full aurix-card-glass rounded-xl p-6 border border-white/[0.08] select-none font-mono">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-white/[0.08] text-slate-500 text-[10px] uppercase tracking-wider">
              <th className="pb-3 pl-2">Action ID & Title</th>
              <th className="pb-3">Domain & Target</th>
              <th className="pb-3">Preflight Gate</th>
              <th className="pb-3">Financial Outlay</th>
              <th className="pb-3">Expected ROI</th>
              <th className="pb-3">Lifecycle State</th>
              <th className="pb-3 text-right pr-2">Governance Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.04]">
            {actions.map((act) => {
              const isAwaiting = act.state === 'AWAITING_APPROVAL';
              const isApproved = act.state === 'APPROVED';
              const isExecuted = act.state === 'EXECUTED';

              return (
                <tr key={act.id} className="hover:bg-white/[0.02] transition-colors">
                  <td className="py-3.5 pl-2">
                    <div className="flex flex-col">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] text-slate-500 font-bold">{act.id}</span>
                        <AurixBadge variant={act.priority === 'CRITICAL' ? 'danger' : 'gold'}>
                          {act.priority}
                        </AurixBadge>
                      </div>
                      <span className="text-white font-bold text-xs mt-1">{act.title}</span>
                    </div>
                  </td>

                  <td className="py-3.5">
                    <span className="text-gold font-bold block">{act.domain}</span>
                    <span className="text-slate-400 text-[10px]">{act.targetEntityName}</span>
                  </td>

                  <td className="py-3.5">
                    {act.preflightCleared ? (
                      <button
                        onClick={() => onOpenPreflight(act)}
                        className="flex items-center gap-1.5 text-[#3DDB91] text-[11px] font-bold hover:underline cursor-pointer"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>CLEARED ({act.preflightChecks.length}/{act.preflightChecks.length})</span>
                      </button>
                    ) : (
                      <span className="text-[#F3B33D] text-[11px] flex items-center gap-1">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        <span>PENDING CHECKS</span>
                      </span>
                    )}
                  </td>

                  <td className="py-3.5">
                    <span className="text-white font-bold">{formatINR(act.prescriptivePayload.financialCommitmentINR)}</span>
                  </td>

                  <td className="py-3.5">
                    <span className="text-[#3DDB91] font-bold">{formatINR(act.prescriptivePayload.expectedRoiINR)}</span>
                  </td>

                  <td className="py-3.5">
                    <AurixBadge
                      variant={isExecuted ? 'success' : isApproved ? 'gold' : isAwaiting ? 'warning' : 'info'}
                      pulse={isAwaiting}
                    >
                      {act.state.replace('_', ' ')}
                    </AurixBadge>
                  </td>

                  <td className="py-3.5 text-right pr-2">
                    <div className="flex items-center justify-end gap-2">
                      {isAwaiting && (
                        <AurixButton variant="gold" size="sm" onClick={() => onOpenPreflight(act)}>
                          <ShieldCheck className="w-3 h-3 mr-1" />
                          <span>REVIEW & SIGN</span>
                        </AurixButton>
                      )}

                      {isApproved && (
                        <>
                          <AurixButton variant="ghost" size="sm" onClick={() => onOpenToken(act)}>
                            <FileKey className="w-3 h-3 text-gold mr-1" />
                            <span>TOKEN</span>
                          </AurixButton>
                          <AurixButton variant="primary" size="sm" onClick={() => onExecute(act.id)}>
                            <Play className="w-3 h-3 mr-1 fill-current" />
                            <span>EXECUTE (P14)</span>
                          </AurixButton>
                        </>
                      )}

                      {isExecuted && act.executionToken && (
                        <AurixButton variant="ghost" size="sm" onClick={() => onOpenToken(act)}>
                          <FileKey className="w-3 h-3 text-[#3DDB91] mr-1" />
                          <span>VERIFY AUDIT</span>
                        </AurixButton>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};