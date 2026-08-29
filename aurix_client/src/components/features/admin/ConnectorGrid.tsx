    'use client';

import React from 'react';
import { EnterpriseConnector } from '@/types/admin.types';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { AurixButton } from '@/components/ui/AurixButton';
import { Cable, RotateCw } from 'lucide-react';

interface ConnectorGridProps {
  connectors: EnterpriseConnector[];
  syncingId: string | null;
  onSync: (id: string) => void;
}

export const ConnectorGrid: React.FC<ConnectorGridProps> = ({
  connectors,
  syncingId,
  onSync,
}) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono select-none">
      {connectors.map((c: any) => {
        const isConnected = c.status === 'CONNECTED';
        const isDegraded = c.status === 'DEGRADED';
        const isSyncing = syncingId === c.connectorId;

        return (
          <div
            key={c.connectorId}
            className={`p-5 rounded-xl border space-y-4 ${
              isDegraded
                ? 'bg-[#FF6B6B]/[0.02] border-[#FF6B6B]/30'
                : 'bg-white/[0.02] border-white/[0.06] hover:border-white/15'
            }`}
          >
            <div className="flex items-start justify-between gap-3 pb-3 border-b border-white/[0.04]">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-lg bg-white/[0.04] border border-white/10 text-gold">
                  <Cable className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-white leading-tight">{c.name}</h4>
                  <span className="text-[10px] text-slate-500">{c.connectorId} • {c.syncFrequency}</span>
                </div>
              </div>

              <AurixBadge variant={isConnected ? 'success' : isDegraded ? 'warning' : 'danger'}>
                {c.status}
              </AurixBadge>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="space-y-0.5">
                <span className="text-[10px] text-slate-500">24H RECORDS SYNCED</span>
                <span className="text-white font-bold block">{c.recordsSyncedLast24h.toLocaleString()} rows</span>
              </div>
              <div className="space-y-0.5">
                <span className="text-[10px] text-slate-500">ERROR RATE</span>
                <span className={c.errorRatePercent > 1.0 ? 'text-[#FF8585] font-bold block' : 'text-[#3DDB91] font-bold block'}>
                  {c.errorRatePercent}%
                </span>
              </div>
            </div>

            <div className="p-2.5 rounded-lg bg-black/40 border border-white/5 text-[11px] text-slate-400 leading-relaxed">
              <span className="text-gold font-bold block text-[10px]">HEALTH & STATUS:</span>
              {c.healthNote}
            </div>

            <div className="pt-2 border-t border-white/[0.04] flex items-center justify-between">
              <span className="text-[10px] text-slate-500">Last Sync: {c.lastSyncTimestamp}</span>
              <AurixButton
                variant="secondary"
                size="sm"
                onClick={() => onSync(c.connectorId)}
                loading={isSyncing}
              >
                <RotateCw className="w-3 h-3 mr-1" />
                <span>MANUAL SYNC</span>
              </AurixButton>
            </div>
          </div>
        );
      })}
    </div>
  );
};