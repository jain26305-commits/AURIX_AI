'use client';

import React from 'react';
import { DataAnomalyItem, QualitySeverity } from '@/types/quality.types';
import { AlertCircle, Search, Wrench } from 'lucide-react';
import { AurixBadge } from '@/components/ui/AurixBadge';

interface AnomalyInspectorTableProps {
  anomalies: DataAnomalyItem[];
  filterSeverity: QualitySeverity | 'all';
  onFilterChange: (severity: QualitySeverity | 'all') => void;
  searchTerm: string;
  onSearchChange: (term: string) => void;
}

export const AnomalyInspectorTable: React.FC<AnomalyInspectorTableProps> = ({
  anomalies,
  filterSeverity,
  onFilterChange,
  searchTerm,
  onSearchChange,
}) => {
  return (
    <div className="w-full aurix-card-glass rounded-xl p-6 border border-white/[0.08] space-y-4">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-white/[0.06]">
        <div>
          <h3 className="text-sm font-semibold text-white tracking-wide flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-[#F3B33D]" />
            DATA INTEGRITY & ANOMALY INSPECTOR
          </h3>
          <p className="text-[11px] font-mono text-slate-400 mt-0.5">
            Transparent provenance log of all anomalies, value corrections, and statistical outliers detected.
          </p>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              placeholder="Search field or SKU..."
              value={searchTerm}
              onChange={(e) => onSearchChange(e.target.value)}
              className="bg-[#15171A] border border-white/10 rounded-lg pl-8 pr-3 py-1 text-xs text-slate-200 font-mono focus:border-[#D4AF37] focus:outline-none w-48"
            />
          </div>

          <div className="flex items-center gap-1 bg-[#15171A] border border-white/10 rounded-lg p-0.5 text-[10px] font-mono">
            {(['all', 'critical', 'warning', 'info'] as const).map((sev) => (
              <button
                key={sev}
                onClick={() => onFilterChange(sev)}
                className={`px-2.5 py-1 rounded-md uppercase font-semibold transition-colors cursor-pointer ${
                  filterSeverity === sev ? 'bg-white/10 text-white' : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                {sev}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs font-mono">
          <thead>
            <tr className="border-b border-white/[0.08] text-slate-500 text-[10px] uppercase tracking-wider">
              <th className="pb-3 pl-2">Severity</th>
              <th className="pb-3">SKU / Entity</th>
              <th className="pb-3">Target Field</th>
              <th className="pb-3">Observed Value</th>
              <th className="pb-3">Expected Rule</th>
              <th className="pb-3 pr-2">Remediation Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.04]">
            {anomalies.map((item: any) => (
              <tr key={item.id} className="hover:bg-white/[0.02] transition-colors">
                <td className="py-3 pl-2">
                  <AurixBadge variant={item.severity === 'critical' ? 'danger' : item.severity === 'warning' ? 'warning' : 'info'}>
                    {item.severity}
                  </AurixBadge>
                </td>
                <td className="py-3 text-white font-medium">
                  {item.skuId || <span className="text-slate-500">GLOBAL_DATASET</span>}
                </td>
                <td className="py-3 text-[#D4AF37]">{item.field}</td>
                <td className="py-3 text-[#FF8585]">
                  {item.valueDetected !== null ? String(item.valueDetected) : '<NULL>'}
                </td>
                <td className="py-3 text-slate-400 text-[11px]">{item.expectedCondition}</td>
                <td className="py-3 pr-2 text-slate-300 text-[11px] flex items-center gap-1.5">
                  <Wrench className="w-3.5 h-3.5 text-gold shrink-0" />
                  <span>{item.remediationAction}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};