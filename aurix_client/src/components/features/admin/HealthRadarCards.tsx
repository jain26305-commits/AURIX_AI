'use client';

import React from 'react';
import { SystemHealthReport } from '@/types/admin.types';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { Activity, Database, Server, Cpu } from 'lucide-react';

export const HealthRadarCards: React.FC<{ report: SystemHealthReport }> = ({ report }) => {
  return (
    <div className="space-y-6 font-mono select-none">
      {/* Top Metrics Ribbon */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <AurixCard title="OVERALL SYSTEM HEALTH" badge={<AurixBadge variant="success">OPTIMAL</AurixBadge>}>
          <div className="flex items-baseline justify-between mt-2">
            <span className="text-2xl font-bold text-[#3DDB91]">{report.overallHealth}</span>
            <Activity className="w-5 h-5 text-[#3DDB91]" />
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Mean API Latency: {report.meanApiLatencyMs} ms</div>
        </AurixCard>

        <AurixCard title="ACTIVE DB CONNECTIONS" badge={<AurixBadge variant="info">POSTGRESQL</AurixBadge>}>
          <div className="flex items-baseline justify-between mt-2">
            <span className="text-2xl font-bold text-white">0{report.activeDatabaseConnections} Conns</span>
            <Database className="w-5 h-5 text-[#D4AF37]" />
          </div>
          <div className="text-[11px] text-slate-400 mt-1">RLS connection pool operating nominally</div>
        </AurixCard>

        <AurixCard title="ASYNC CELERY QUEUE" badge={<AurixBadge variant="gold">WORKERS</AurixBadge>}>
          <div className="flex items-baseline justify-between mt-2">
            <span className="text-2xl font-bold text-gold">0{report.celeryQueueDepth} Tasks</span>
            <Server className="w-5 h-5 text-gold" />
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Worker queue latency &lt; 2ms</div>
        </AurixCard>
      </div>

      {/* Services Grid */}
      <div className="w-full aurix-card-glass rounded-xl p-6 border border-white/[0.08] space-y-4">
        <h3 className="text-sm font-bold text-white tracking-wide flex items-center gap-2">
          <Cpu className="w-4 h-4 text-gold" />
          MICROSERVICE & WORKER OBSERVABILITY
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {report.services.map((srv) => (
            <div key={srv.serviceKey} className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06] space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-white font-bold text-xs block">{srv.serviceName}</span>
                  <span className="text-slate-500 text-[10px]">{srv.serviceKey}</span>
                </div>
                <AurixBadge variant={srv.status === 'HEALTHY' ? 'success' : 'danger'}>
                  {srv.status}
                </AurixBadge>
              </div>

              <div className="grid grid-cols-3 gap-2 text-center pt-2 border-t border-white/[0.04] text-xs">
                <div>
                  <span className="text-[9px] text-slate-500 uppercase block">LATENCY</span>
                  <span className="text-white font-bold">{srv.latencyMs} ms</span>
                </div>
                <div>
                  <span className="text-[9px] text-slate-500 uppercase block">UPTIME</span>
                  <span className="text-[#3DDB91] font-bold">{srv.uptimePercent}%</span>
                </div>
                <div>
                  <span className="text-[9px] text-slate-500 uppercase block">UTILIZATION</span>
                  <span className="text-gold font-bold">{srv.resourceUtilizationPercent}%</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};