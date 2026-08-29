'use client';

import React from 'react';
import { OperationalAlert } from '@/types/alert.types';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { AurixButton } from '@/components/ui/AurixButton';
import { CheckCircle2, FolderPlus } from 'lucide-react';
import { formatINR } from '@/lib/formatters';

interface AlertFeedTableProps {
  alerts: OperationalAlert[];
  onAcknowledge: (id: string) => void;
  onEscalate: (id: string) => void;
}

export const AlertFeedTable: React.FC<AlertFeedTableProps> = ({
  alerts,
  onAcknowledge,
  onEscalate,
}) => {
  return (
    <div className="w-full aurix-card-glass rounded-xl p-6 border border-white/[0.08] select-none">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs font-mono">
          <thead>
            <tr className="border-b border-white/[0.08] text-slate-500 text-[10px] uppercase tracking-wider">
              <th className="pb-3 pl-2">Severity & ID</th>
              <th className="pb-3">Operational Signal</th>
              <th className="pb-3">Domain & Target</th>
              <th className="pb-3">Exposure</th>
              <th className="pb-3">Breach Window</th>
              <th className="pb-3">Status</th>
              <th className="pb-3 text-right pr-2">Triage Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.04]">
            {alerts.map((a) => {
              const isCritical = a.severity === 'CRITICAL';
              const isWarning = a.severity === 'WARNING';

              return (
                <tr key={a.id} className="hover:bg-white/[0.02] transition-colors">
                  <td className="py-3.5 pl-2">
                    <div className="flex items-center gap-2">
                      <AurixBadge
                        variant={isCritical ? 'danger' : isWarning ? 'warning' : 'info'}
                        pulse={isCritical && a.status === 'ACTIVE'}
                      >
                        {a.severity}
                      </AurixBadge>
                      <span className="text-[10px] text-slate-500">{a.id}</span>
                    </div>
                  </td>

                  <td className="py-3.5 max-w-md">
                    <span className="text-white font-bold block">{a.title}</span>
                    <span className="text-slate-400 text-[11px] mt-0.5 block leading-relaxed">{a.summary}</span>
                    <span className="text-[9px] text-slate-500 mt-1 block">
                      Trigger: {a.provenance.ruleOrModel} ({a.provenance.actualValue})
                    </span>
                  </td>

                  <td className="py-3.5">
                    <span className="text-gold font-bold block">{a.domain}</span>
                    <span className="text-slate-400 text-[10px]">{a.entityName} ({a.entityId})</span>
                  </td>

                  <td className="py-3.5">
                    <span className="text-white font-bold">{formatINR(a.exposureINR)}</span>
                  </td>

                  <td className="py-3.5">
                    <span className={isCritical ? 'text-[#FF6B6B] font-bold' : 'text-slate-300'}>
                      {a.breachWindow}
                    </span>
                  </td>

                  <td className="py-3.5">
                    <span className="text-slate-400 text-[10px] font-semibold uppercase">{a.status}</span>
                    {a.linkedCaseId && (
                      <span className="text-gold text-[9px] block">➔ {a.linkedCaseId}</span>
                    )}
                  </td>

                  <td className="py-3.5 text-right pr-2">
                    <div className="flex items-center justify-end gap-2">
                      {a.status === 'ACTIVE' && (
                        <AurixButton variant="secondary" size="sm" onClick={() => onAcknowledge(a.id)}>
                          <CheckCircle2 className="w-3 h-3 mr-1" />
                          <span>ACK</span>
                        </AurixButton>
                      )}
                      {!a.linkedCaseId && a.status !== 'DISMISSED' && (
                        <AurixButton variant="gold" size="sm" onClick={() => onEscalate(a.id)}>
                          <FolderPlus className="w-3 h-3 mr-1" />
                          <span>CREATE CASE</span>
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