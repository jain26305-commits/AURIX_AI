'use client';

import React from 'react';
import { ShieldCheck, Radio } from 'lucide-react';
import { AurixBadge } from '@/components/ui/AurixBadge';

export interface DomainKpi {
  label: string;
  value: string | number;
  delta?: string;
  deltaType?: 'positive' | 'negative' | 'neutral';
  provenance?: string;
}

export interface DomainLandingHeroProps {
  domainTag: string;
  title: string;
  description: string;
  kpis?: DomainKpi[];
  status?: 'OPTIMAL' | 'DEGRADED' | 'WATCH' | 'CRITICAL';
  telemetryStream?: string;
}

export const DomainLandingHero: React.FC<DomainLandingHeroProps> = ({
  domainTag,
  title,
  description,
  kpis = [],
  status = 'OPTIMAL',
  telemetryStream = 'LIVE FEED',
}) => {
  const getStatusBadge = () => {
    switch (status) {
      case 'CRITICAL':
        return <AurixBadge variant="danger" pulse>CRITICAL ANOMALY</AurixBadge>;
      case 'WATCH':
      case 'DEGRADED':
        return <AurixBadge variant="warning" pulse>ATTENTION REQUIRED</AurixBadge>;
      case 'OPTIMAL':
      default:
        return <AurixBadge variant="success" pulse>SYSTEM NOMINAL</AurixBadge>;
    }
  };

  return (
    <div className="p-6 md:p-8 rounded-2xl aurix-card-glass border border-white/[0.08] relative overflow-hidden space-y-6 shadow-2xl animate-pure-fade">
      <div className="absolute top-0 right-0 w-[450px] h-[350px] bg-[radial-gradient(ellipse_at_top_right,rgba(212,175,55,0.09)_0%,transparent_70%)] pointer-events-none" />
      <div className="absolute -bottom-10 -left-10 w-[300px] h-[200px] bg-[radial-gradient(circle,rgba(255,255,255,0.02)_0%,transparent_60%)] pointer-events-none" />

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
        <div>
          <div className="flex items-center gap-2 font-mono text-[10px] text-[#D4AF37] font-bold tracking-[0.3em] uppercase mb-1.5">
            <span className="bg-[#D4AF37]/10 px-2 py-0.5 rounded border border-[#D4AF37]/30">DOMAIN {domainTag}</span>
            <span>•</span>
            <span className="flex items-center gap-1 text-[#3DDB91]">
              <Radio className="w-3 h-3 animate-pulse" /> {telemetryStream}
            </span>
          </div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-wide uppercase drop-shadow-[0_0_15px_rgba(212,175,55,0.15)]">
            {title}
          </h1>
          <p className="text-xs md:text-sm text-slate-400 max-w-3xl mt-2 font-sans leading-relaxed">
            {description}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5 self-start md:self-auto font-mono text-[10px]">
          {getStatusBadge()}
          <div className="flex items-center gap-1.5 bg-white/[0.03] border border-white/[0.08] px-3 py-1 rounded-md text-slate-300">
            <ShieldCheck className="w-3.5 h-3.5 text-[#3DDB91]" />
            <span>RLS ISOLATED</span>
          </div>
        </div>
      </div>

      {kpis.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-4 border-t border-white/[0.06] relative z-10">
          {kpis.map((kpi, idx) => (
            <div
              key={idx}
              className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.04] hover:border-[#D4AF37]/30 hover:bg-[#D4AF37]/[0.02] transition-all duration-300 space-y-1.5 group"
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block group-hover:text-slate-300 transition-colors truncate">
                  {kpi.label}
                </span>
                {kpi.provenance && (
                  <span className="text-[8px] font-mono text-slate-600 bg-white/[0.03] px-1 rounded">
                    {kpi.provenance}
                  </span>
                )}
              </div>
              <div className="flex items-baseline justify-between gap-2">
                <span className="text-xl font-mono font-extrabold text-white tracking-tight group-hover:text-[#D4AF37] transition-colors">
                  {kpi.value}
                </span>
                {kpi.delta && (
                  <span
                    className={`text-[10px] font-mono font-bold shrink-0 ${
                      kpi.deltaType === 'positive'
                        ? 'text-[#3DDB91]'
                        : kpi.deltaType === 'negative'
                        ? 'text-[#FF6B6B]'
                        : 'text-slate-400'
                    }`}
                  >
                    {kpi.delta}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
