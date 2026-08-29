'use client';

import React from 'react';
import { DomainWorkspaceOrchestrator } from '@/components/domain/DomainWorkspaceOrchestrator';
import { FinancialImpactExposureCard } from '@/components/features/control-tower/FinancialImpactExposureCard';
import { ControlTowerHealthGrid } from '@/components/features/control-tower/ControlTowerHealthGrid';
import { TopSignalsActionFeed } from '@/components/features/control-tower/TopSignalsActionFeed';
import { DataBoundary } from '@/components/states/DataBoundary';
import { useControlTower } from '@/hooks/useControlTower';
import { useAdminSystemHealth } from '@/hooks/useAdminSystemHealth';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { Activity, Server, Cpu, Database, CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';

export default function OverviewPage() {
  const { data: report, loading: isLoading, reload: reloadControlTower } = useControlTower();
  const { report: systemHealth, loading: healthLoading, reload: reloadHealth } = useAdminSystemHealth();

  return (
    <DomainWorkspaceOrchestrator
      domainKey="overview"
      renderWorkspace={(subdomainId) => (
        <>
          {subdomainId === 'summary' && (
            <DataBoundary
              isLoading={isLoading}
              isError={!isLoading && !report}
              errorMessage="Failed to synchronize with the enterprise control tower stream."
              onRetry={reloadControlTower}
              loadingMessage="AGGREGATING CROSS-DOMAIN ENTERPRISE TELEMETRY..."
            >
              {report && (
                <div className="space-y-6 animate-pure-fade">
                  <FinancialImpactExposureCard financials={report.financials} />
                  <ControlTowerHealthGrid pillars={report.pillars} />
                  <TopSignalsActionFeed signals={report.urgentSignals} />
                </div>
              )}
            </DataBoundary>
          )}

          {subdomainId === 'telemetry' && (
            <DataBoundary
              isLoading={healthLoading}
              isError={!healthLoading && !systemHealth}
              errorMessage="Failed to load real-time system health and service telemetry."
              onRetry={reloadHealth}
              loadingMessage="GATHERING CLUSTER HEALTH TELEMETRY..."
            >
              {systemHealth && (
                <div className="space-y-6 animate-pure-fade">
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 font-mono">
                    <AurixCard
                      title="API GATEWAY LATENCY"
                      badge={
                        <AurixBadge
                          variant={systemHealth.overallHealth === 'HEALTHY' ? 'success' : 'warning'}
                        >
                          {systemHealth.overallHealth}
                        </AurixBadge>
                      }
                    >
                      <div className="flex items-center gap-3 mt-2">
                        <Server className="w-5 h-5 text-[#3DDB91]" />
                        <span className="text-xl font-bold text-white">
                          {systemHealth.meanApiLatencyMs.toFixed(1)} ms
                        </span>
                      </div>
                      <span className="text-[10px] text-slate-500 mt-1 block">
                        Mean Gateway Latency Percentile
                      </span>
                    </AurixCard>

                    <AurixCard title="CELERY QUEUE DEPTH" badge={<AurixBadge variant="gold">ASYNC BROKER</AurixBadge>}>
                      <div className="flex items-center gap-3 mt-2">
                        <Activity className="w-5 h-5 text-[#D4AF37]" />
                        <span className="text-xl font-bold text-white">
                          {systemHealth.celeryQueueDepth} Tasks
                        </span>
                      </div>
                      <span className="text-[10px] text-slate-500 mt-1 block">
                        Active In-Flight Message Queue
                      </span>
                    </AurixCard>

                    <AurixCard title="DB CONNECTION POOL" badge={<AurixBadge variant="info">POSTGRES RLS</AurixBadge>}>
                      <div className="flex items-center gap-3 mt-2">
                        <Database className="w-5 h-5 text-[#38BDF8]" />
                        <span className="text-xl font-bold text-white">
                          {systemHealth.activeDatabaseConnections} Active
                        </span>
                      </div>
                      <span className="text-[10px] text-slate-500 mt-1 block">
                        Dedicated Pool Leases
                      </span>
                    </AurixCard>

                    <AurixCard title="SYSTEM EVALUATION" badge={<AurixBadge variant="gold">TIMESTAMP</AurixBadge>}>
                      <div className="flex items-center gap-3 mt-2">
                        <Cpu className="w-5 h-5 text-[#D4AF37]" />
                        <span className="text-sm font-bold text-white truncate">
                          {new Date(systemHealth.evaluatedAt).toLocaleTimeString()}
                        </span>
                      </div>
                      <span className="text-[10px] text-slate-500 mt-1 block">
                        Telemetry Polling Cycle
                      </span>
                    </AurixCard>
                  </div>

                  <AurixCard
                    title="MICROSERVICE CLUSTER HEALTH & STATUS"
                    badge={
                      <AurixBadge variant="gold">
                        {systemHealth.services ? systemHealth.services.length : 0} SERVICES
                      </AurixBadge>
                    }
                  >
                    <div className="space-y-2 pt-2 font-mono text-xs">
                      {systemHealth.services && systemHealth.services.length > 0 ? (
                        systemHealth.services.map((svc) => {
                          const isHealthy = svc.status === 'HEALTHY';
                          const isDegraded = svc.status === 'DEGRADED';

                          return (
                            <div
                              key={svc.serviceKey}
                              className="flex items-center justify-between p-3 rounded-lg bg-white/[0.02] border border-white/[0.05]"
                            >
                              <div className="flex items-center gap-3">
                                {isHealthy ? (
                                  <CheckCircle2 className="w-4 h-4 text-[#3DDB91] shrink-0" />
                                ) : isDegraded ? (
                                  <AlertTriangle className="w-4 h-4 text-[#F3B33D] shrink-0" />
                                ) : (
                                  <XCircle className="w-4 h-4 text-[#FF6B6B] shrink-0" />
                                )}
                                <div>
                                  <span className="text-white font-bold block">{svc.serviceName}</span>
                                  <span className="text-[10px] text-slate-500 font-sans">
                                    Latency: {svc.latencyMs}ms • Uptime: {svc.uptimePercent}%
                                  </span>
                                </div>
                              </div>

                              <div className="flex items-center gap-3">
                                <span className="text-[10px] text-slate-400">
                                  Load: {svc.resourceUtilizationPercent}%
                                </span>
                                <AurixBadge
                                  variant={isHealthy ? 'success' : isDegraded ? 'warning' : 'danger'}
                                  size="sm"
                                >
                                  {svc.status}
                                </AurixBadge>
                              </div>
                            </div>
                          );
                        })
                      ) : (
                        <div className="p-4 text-center text-slate-500 text-xs">
                          NO MICROSERVICE INSTANCES REPORTING TELEMETRY
                        </div>
                      )}
                    </div>
                  </AurixCard>
                </div>
              )}
            </DataBoundary>
          )}
        </>
      )}
    />
  );
}
