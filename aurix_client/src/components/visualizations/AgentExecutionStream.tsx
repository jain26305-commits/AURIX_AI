'use client';

import React from 'react';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { Terminal } from 'lucide-react';

export const AgentExecutionStream: React.FC = () => {
  const traces = [
    { time: '18:42:01', agent: 'INVENTORY_OPTIMIZER_V4', action: 'TOOL_CALL: fetch_safety_stock_deficit(sku="SKU-001")', status: 'SUCCESS', latency: '124ms' },
    { time: '18:42:04', agent: 'PRESCRIPTION_SOLVER', action: 'REASONING: Evaluating (s, S) policy buffer against Tier-1 supplier lead time variance.', status: 'INFO', latency: '48ms' },
    { time: '18:42:09', agent: 'ACTION_EXECUTOR', action: 'PREFLIGHT_VERIFY: Cryptographic signature valid. RLS tenant policy enforced.', status: 'CLEARED', latency: '18ms' },
    { time: '18:42:15', agent: 'ERP_DISPATCH_GATEWAY', action: 'POST: /api/v1/orders/replenishment (PO #2026-9812)', status: 'DISPATCHED', latency: '340ms' },
  ];

  return (
    <div className="space-y-6">
      <AurixCard
        title="LIVE AGENT RUNTIME STREAM"
        subtitle="Cryptographically verified reasoning traces, function arguments, and tool outputs"
        badge={<AurixBadge variant="gold">PHASE 29 RUNTIME</AurixBadge>}
        className="space-y-4"
      >
        <div className="p-4 rounded-xl bg-[#030303] border border-white/[0.08] font-mono text-xs space-y-3">
          <div className="flex items-center justify-between border-b border-white/[0.06] pb-2 text-[10px] text-slate-500">
            <span className="flex items-center gap-2 text-[#3DDB91]">
              <Terminal className="w-3.5 h-3.5" /> STREAMING LIVE TERMINAL
            </span>
            <span>TOKEN CONSUMPTION: 4,280 / 100,000</span>
          </div>

          <div className="space-y-2.5">
            {traces.map((trace, idx) => (
              <div key={idx} className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-2 rounded bg-white/[0.02] border border-white/[0.03]">
                <div className="flex items-center gap-2">
                  <span className="text-slate-600 text-[10px]">{trace.time}</span>
                  <span className="text-[#D4AF37] font-bold text-[10px]">{trace.agent}</span>
                  <span className="text-slate-300 text-xs truncate max-w-xl">{trace.action}</span>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-[10px] text-slate-500">{trace.latency}</span>
                  <AurixBadge variant="success" size="sm">{trace.status}</AurixBadge>
                </div>
              </div>
            ))}
          </div>
        </div>
      </AurixCard>
    </div>
  );
};
