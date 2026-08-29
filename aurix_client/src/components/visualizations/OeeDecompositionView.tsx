'use client';

import React from 'react';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';

export const OeeDecompositionView: React.FC = () => {
  const workCenters = [
    { id: 'WC-01', name: 'Circular Knitting Hall A', availability: '94.2%', performance: '96.1%', quality: '99.4%', oee: '89.9%', status: 'OPTIMAL' },
    { id: 'WC-02', name: 'Dyeing & Bleaching Mill', availability: '88.4%', performance: '91.2%', quality: '97.8%', oee: '78.8%', status: 'WATCH' },
    { id: 'WC-03', name: 'Precision Laser Cutting', availability: '98.1%', performance: '97.4%', quality: '99.8%', oee: '95.4%', status: 'OPTIMAL' },
    { id: 'WC-04', name: 'Stitching & Assembly Line 1', availability: '79.2%', performance: '84.0%', quality: '96.1%', oee: '63.9%', status: 'BOTTLENECK' },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {workCenters.map((wc) => {
          const isBottleneck = wc.status === 'BOTTLENECK';
          return (
            <AurixCard
              key={wc.id}
              variant="interactive"
              className={`p-4 space-y-3 ${
                isBottleneck ? 'border-[#FF6B6B]/50 shadow-[0_0_20px_rgba(255,107,107,0.15)]' : 'border-white/[0.06]'
              }`}
            >
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-[10px] font-mono text-[#D4AF37] font-bold">{wc.id}</span>
                  <h4 className="text-xs font-bold text-white uppercase font-mono truncate max-w-[140px]">{wc.name}</h4>
                </div>
                <AurixBadge variant={isBottleneck ? 'danger' : wc.status === 'WATCH' ? 'warning' : 'success'}>
                  {wc.status}
                </AurixBadge>
              </div>

              <div className="p-2.5 rounded bg-white/[0.02] border border-white/[0.04] text-center">
                <span className="text-[9px] font-mono text-slate-500 uppercase block">COMPOSITE OEE</span>
                <span className="text-xl font-mono font-extrabold text-white">{wc.oee}</span>
              </div>

              <div className="space-y-1 font-mono text-[10px]">
                <div className="flex justify-between text-slate-400">
                  <span>AVAILABILITY:</span>
                  <span className="text-white font-bold">{wc.availability}</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>PERFORMANCE:</span>
                  <span className="text-white font-bold">{wc.performance}</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>QUALITY YIELD:</span>
                  <span className="text-[#3DDB91] font-bold">{wc.quality}</span>
                </div>
              </div>
            </AurixCard>
          );
        })}
      </div>
    </div>
  );
};
