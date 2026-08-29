'use client';

import React from 'react';
import { ColumnMappingItem } from '@/types/data-intake.types';
import { Check, AlertTriangle, ArrowRight, Database } from 'lucide-react';
import { AurixBadge } from '@/components/ui/AurixBadge';

interface SchemaMapperGridProps {
  mappings: ColumnMappingItem[];
  availableRawColumns: string[];
  onMappingChange: (canonicalKey: string, newRawColumn: string) => void;
}

export const SchemaMapperGrid: React.FC<SchemaMapperGridProps> = ({
  mappings,
  availableRawColumns,
  onMappingChange,
}) => {
  const getConfidenceBadge = (confidenceStr: string) => {
    const c = (confidenceStr || '').toLowerCase();
    if (c === 'exact') return <AurixBadge variant="success">EXACT</AurixBadge>;
    if (c === 'high') return <AurixBadge variant="info">HIGH</AurixBadge>;
    if (c === 'medium' || c === 'suggested') return <AurixBadge variant="gold">SUGGESTED</AurixBadge>;
    if (c === 'manual') return <AurixBadge variant="neutral">MANUAL</AurixBadge>;
    return <AurixBadge variant="danger">NONE</AurixBadge>;
  };

  return (
    <div className="w-full aurix-card-glass rounded-xl p-6 border border-white/[0.08]">
      <div className="flex items-center justify-between pb-4 mb-4 border-b border-white/[0.06]">
        <div>
          <h3 className="text-sm font-semibold text-white tracking-wide flex items-center gap-2">
            <Database className="w-4 h-4 text-gold" />
            CANONICAL SCHEMA MAPPING
          </h3>
          <p className="text-[11px] font-mono text-slate-400 mt-0.5">
            Confirm or remap incoming raw file headers to deterministic AURIX pipeline entities.
          </p>
        </div>
        <AurixBadge variant="info">
          {mappings.filter((m) => m.status === 'valid').length} / {mappings.length} MAPPED
        </AurixBadge>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs font-mono">
          <thead>
            <tr className="border-b border-white/[0.08] text-slate-500 text-[10px] uppercase tracking-wider">
              <th className="pb-3 pl-2">Canonical Target Entity</th>
              <th className="pb-3">Type</th>
              <th className="pb-3 text-center">Pipeline</th>
              <th className="pb-3">Detected Source Column</th>
              <th className="pb-3">Confidence</th>
              <th className="pb-3 text-right pr-2">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.04]">
            {mappings.map((item: any) => (
              <tr key={item.canonicalKey} className="hover:bg-white/[0.02] transition-colors group">
                <td className="py-3 pl-2">
                  <div className="flex flex-col">
                    <span className="text-white font-medium flex items-center gap-1.5">
                      {item.canonicalLabel || item.canonicalName || item.canonicalKey}
                      {item.required && <span className="text-[#FF6B6B] text-[10px]">*</span>}
                    </span>
                    <span className="text-[10px] text-slate-500">{item.canonicalKey}</span>
                  </div>
                </td>

                <td className="py-3 text-slate-400">
                  <span className="px-2 py-0.5 rounded bg-white/[0.03] border border-white/[0.06] text-[10px]">
                    {item.dataType || 'STRING'}
                  </span>
                </td>

                <td className="py-3 text-center text-slate-600 group-hover:text-gold transition-colors">
                  <ArrowRight className="w-3.5 h-3.5 inline-block" />
                </td>

                <td className="py-3">
                  <select
                    value={item.detectedColumn || 'UNMAPPED'}
                    onChange={(e) => onMappingChange(item.canonicalKey, e.target.value)}
                    className="bg-[#15171A] border border-white/15 rounded-lg px-3 py-1.5 text-xs text-slate-200 font-mono focus:border-[#D4AF37] focus:outline-none cursor-pointer"
                  >
                    <option value="UNMAPPED">-- UNMAPPED --</option>
                    {availableRawColumns.map((col) => (
                      <option key={col} value={col}>
                        {col}
                      </option>
                    ))}
                  </select>
                </td>

                <td className="py-3">
                  {getConfidenceBadge(item.confidence)}
                </td>

                <td className="py-3 text-right pr-2">
                  {item.status === 'valid' && (
                    <span className="inline-flex items-center gap-1 text-[#3DDB91] text-[11px]">
                      <Check className="w-3.5 h-3.5" /> Valid
                    </span>
                  )}
                  {item.status === 'missing' && (
                    <span className="inline-flex items-center gap-1 text-[#FF6B6B] text-[11px]">
                      <AlertTriangle className="w-3.5 h-3.5" /> Required
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};