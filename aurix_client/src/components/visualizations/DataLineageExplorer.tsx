'use client';

import React from 'react';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { Database } from 'lucide-react';

export const DataLineageExplorer: React.FC = () => {
  const connectors = [
    { name: 'SAP S/4HANA Enterprise', type: 'ERP', status: 'HEALTHY', recordsIngested: '24,000', latency: '42s ago' },
    { name: 'Odoo v17 Supply Chain', type: 'WMS', status: 'HEALTHY', recordsIngested: '18,400', latency: '1m ago' },
    { name: 'Tally Prime Financials', type: 'ACCOUNTING', status: 'HEALTHY', recordsIngested: '8,200', latency: '3m ago' },
    { name: 'Carrier EDI & Telematics', type: 'TMS', status: 'STREAMING', recordsIngested: '64,200', latency: 'Live' },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {connectors.map((conn) => (
          <AurixCard key={conn.name} variant="interactive" className="p-4 space-y-3 border-white/[0.06]">
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-center gap-2">
                <Database className="w-4 h-4 text-[#D4AF37]" />
                <span className="text-xs font-bold text-white uppercase font-mono">{conn.name}</span>
              </div>
              <AurixBadge variant="success" size="sm">{conn.status}</AurixBadge>
            </div>

            <div className="space-y-1 pt-2 border-t border-white/[0.04] font-mono text-[10px]">
              <div className="flex justify-between text-slate-400">
                <span>SYSTEM TYPE:</span>
                <span className="text-white font-bold">{conn.type}</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>INGESTED (24H):</span>
                <span className="text-slate-300">{conn.recordsIngested}</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>LAST SYNC:</span>
                <span className="text-[#3DDB91]">{conn.latency}</span>
              </div>
            </div>
          </AurixCard>
        ))}
      </div>
    </div>
  );
};
