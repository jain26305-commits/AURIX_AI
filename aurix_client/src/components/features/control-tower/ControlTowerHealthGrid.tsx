'use client';

import React from 'react';
import Link from 'next/link';
import { PillarHealthItem } from '@/types/control-tower.types';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { ArrowUpRight } from 'lucide-react';

interface ControlTowerHealthGridProps {
  pillars: PillarHealthItem[];
}

export const ControlTowerHealthGrid: React.FC<ControlTowerHealthGridProps> = ({ pillars }) => {
  return (
    <div className="space-y-3 select-none">
      <div className="flex items-center justify-between pb-2 border-b border-white/[0.06]">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[#D4AF37] animate-signal-beacon" />
          <h3 className="text-xs font-mono font-bold uppercase tracking-widest text-white">
            8-PILLAR STRATEGIC HEALTH RADAR
          </h3>
        </div>
        <span className="text-[10px] font-mono text-slate-500">REAL-TIME DETERMINISTIC TELEMETRY</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {pillars.map((p) => {
          const isWatch = p.status === 'WATCH';
          const isCritical = p.status === 'CRITICAL';

          return (
            <Link
              key={p.key}
              href={p.routeHref}
              className={`aurix-card-glass rounded-xl p-4 border transition-all duration-300 flex flex-col justify-between group relative overflow-hidden ${
                isCritical
                  ? 'border-[#FF6B6B]/40 hover:border-[#FF6B6B] bg-[#FF6B6B]/[0.03]'
                  : isWatch
                  ? 'border-[#F3B33D]/30 hover:border-[#F3B33D] bg-[#F3B33D]/[0.02]'
                  : 'border-white/[0.08] hover:border-white/20'
              }`}
            >
              {/* Top Accent Indicator */}
              <div
                className={`absolute inset-x-0 top-0 h-[2px] ${
                  isCritical ? 'bg-[#FF6B6B]' : isWatch ? 'bg-[#F3B33D]' : 'bg-[#3DDB91]'
                }`}
              />

              <div>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-white tracking-wide">{p.title}</span>
                  <AurixBadge
                    variant={isCritical ? 'danger' : isWatch ? 'warning' : 'success'}
                    pulse={isCritical}
                  >
                    {p.status}
                  </AurixBadge>
                </div>

                <div className="mt-3">
                  <span className="text-xl font-bold font-mono text-white tracking-tight block">
                    {p.primaryMetric}
                  </span>
                  <span className="text-[10px] font-mono text-slate-500 uppercase">{p.metricLabel}</span>
                </div>

                <p className="text-[11px] font-mono text-slate-400 mt-2 leading-relaxed line-clamp-2">
                  {p.subText}
                </p>
              </div>

              <div className="mt-4 pt-3 border-t border-white/[0.04] flex items-center justify-between text-[10px] font-mono text-slate-400 group-hover:text-white transition-colors">
                <span>INSPECT PILLAR</span>
                <ArrowUpRight className="w-3.5 h-3.5 text-gold group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
};