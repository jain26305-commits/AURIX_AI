'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { QualityScoreGauge } from '@/components/features/data-quality/QualityScoreGauge';
import { DimensionAuditCard } from '@/components/features/data-quality/DimensionAuditCard';
import { ReadinessMatrix } from '@/components/features/data-quality/ReadinessMatrix';
import { AnomalyInspectorTable } from '@/components/features/data-quality/AnomalyInspectorTable';
import { useQualityAssessment } from '@/hooks/useQualityAssessment';
import { AurixButton } from '@/components/ui/AurixButton';
import { ArrowRight, RotateCw } from 'lucide-react';
import { useWorkspaceHeader } from '@/context/WorkspaceHeaderContext';

export default function DataQualityPage() {
  useWorkspaceHeader({ activeWorkspaceTitle: "Data Quality" });
  const router = useRouter();
  const {
    report,
    loading,
    selectedSeverityFilter,
    setSelectedSeverityFilter,
    searchTerm,
    setSearchTerm,
    filteredAnomalies,
    reloadReport,
  } = useQualityAssessment();

  if (loading || !report) {
    return (
      <>
        <div className="py-24 flex flex-col items-center justify-center text-center space-y-4">
          <div className="w-8 h-8 rounded-full border-2 border-[#D4AF37] border-t-transparent animate-spin" />
          <p className="text-xs font-mono text-slate-400 tracking-widest uppercase">
            AUDITING 7-DIMENSION DATA INTEGRITY...
          </p>
        </div>
      </>
    );
  }

  return (
    <>
      <div className="space-y-8 animate-pure-fade">
        {/* Workspace Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-white tracking-wide">DATA QUALITY & ANALYTICAL READINESS</h1>
            <p className="text-xs font-mono text-slate-400 mt-1">
              Deterministic health evaluation and execution clearance for downstream ML & forecasting models.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <AurixButton variant="secondary" size="sm" onClick={reloadReport}>
              <RotateCw className="w-3.5 h-3.5 mr-1.5" /> RE-AUDIT
            </AurixButton>
            <AurixButton variant="gold" size="sm" onClick={() => router.push('/data/eda')}>
              <span>PROCEED TO EDA</span>
              <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
            </AurixButton>
          </div>
        </div>

        {/* 1. Overall DQ Metric Gauge */}
        <QualityScoreGauge
          score={report.overallScore}
          health={report.overallHealth}
          totalRows={report.totalRowsAudited}
          totalCols={report.totalColumnsAudited}
          temporalStart={report.temporalRange.start}
          temporalEnd={report.temporalRange.end}
        />

        {/* 2. Analytical Module Readiness Matrix */}
        <ReadinessMatrix items={report.readinessMatrix} />

        {/* 3. 7-Dimension Breakdown */}
        <DimensionAuditCard dimensions={report.dimensions} />

        {/* 4. Anomaly and Correction Inspector */}
        <AnomalyInspectorTable
          anomalies={filteredAnomalies}
          filterSeverity={selectedSeverityFilter}
          onFilterChange={setSelectedSeverityFilter}
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
        />
      </div>
    </>
  );
}