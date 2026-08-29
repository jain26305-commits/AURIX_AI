'use client';

import React from 'react';
import { SystemAuditLogEntry } from '@/types/admin.types';
import { AurixBadge } from '@/components/ui/AurixBadge';

export const AuditLogTable: React.FC<{ logs: SystemAuditLogEntry[] }> = ({ logs }) => {
  return (
    <div className="w-full aurix-card-glass rounded-xl p-6 border border-white/[0.08] select-none font-mono">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-white/[0.08] text-slate-500 text-[10px] uppercase tracking-wider">
              <th className="pb-3 pl-2">Timestamp & ID</th>
              <th className="pb-3">Actor & Role</th>
              <th className="pb-3">Category</th>
              <th className="pb-3">Event Summary</th>
              <th className="pb-3">Source IP</th>
              <th className="pb-3 text-right pr-2">Outcome</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.04]">
            {logs.map((l) => (
              <tr key={l.logId} className="hover:bg-white/[0.02] transition-colors">
                <td className="py-3.5 pl-2">
                  <span className="text-white font-bold block">{l.timestamp}</span>
                  <span className="text-slate-500 text-[10px]">{l.logId}</span>
                </td>

                <td className="py-3.5">
                  <span className="text-slate-200 font-bold block">{l.actorEmail}</span>
                  <span className="text-gold text-[10px]">{l.actorRole}</span>
                </td>

                <td className="py-3.5">
                  <AurixBadge variant="info">{l.actionCategory}</AurixBadge>
                </td>

                <td className="py-3.5 text-slate-300 text-[11px] max-w-md leading-relaxed">
                  {l.eventSummary}
                </td>

                <td className="py-3.5 text-slate-500">{l.ipAddress}</td>

                <td className="py-3.5 text-right pr-2">
                  <AurixBadge variant={l.resultStatus === 'SUCCESS' ? 'success' : 'danger'}>
                    {l.resultStatus}
                  </AurixBadge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};