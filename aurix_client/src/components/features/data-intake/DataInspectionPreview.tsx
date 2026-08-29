'use client';

import React from 'react';
import { DataInspectionRow, IngestionMetadata } from '@/types/data-intake.types';
import { Table, FileText } from 'lucide-react';

interface DataInspectionPreviewProps {
  metadata: IngestionMetadata;
  rows: DataInspectionRow[];
}

export const DataInspectionPreview: React.FC<DataInspectionPreviewProps> = ({ metadata, rows }) => {
  if (rows.length === 0) return null;

  const headers = Object.keys(rows[0]);

  return (
    <div className="w-full aurix-card-glass rounded-xl p-6 border border-white/[0.08]">
      <div className="flex items-center justify-between pb-4 mb-4 border-b border-white/[0.06]">
        <div>
          <h3 className="text-sm font-semibold text-white tracking-wide flex items-center gap-2">
            <Table className="w-4 h-4 text-[#D4AF37]" />
            DATA INSPECTION PREVIEW
          </h3>
          <p className="text-[11px] font-mono text-slate-400 mt-0.5">
            Initial records parsed from <span className="text-white font-medium">{metadata.fileName}</span> ({metadata.rowCount} total rows detected).
          </p>
        </div>

        <div className="flex items-center gap-3 text-xs font-mono text-slate-400">
          <span className="flex items-center gap-1">
            <FileText className="w-3.5 h-3.5 text-gold" /> {(((metadata.fileSizeBytes ?? 0)) / 1024).toFixed(1)} KB
          </span>
        </div>
      </div>

      <div className="overflow-x-auto max-h-72">
        <table className="w-full text-left text-xs font-mono">
          <thead className="sticky top-0 bg-[#0C0E12]/95 backdrop-blur-md z-10">
            <tr className="border-b border-white/[0.08] text-slate-400 text-[10px] uppercase tracking-wider">
              <th className="pb-2.5 pl-2">#</th>
              {headers.map((h) => (
                <th key={h} className="pb-2.5 px-3">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.03]">
            {rows.map((row, idx) => (
              <tr key={idx} className="hover:bg-white/[0.02] transition-colors">
                <td className="py-2.5 pl-2 text-slate-600 text-[10px]">{idx + 1}</td>
                {headers.map((h) => (
                  <td key={h} className="py-2.5 px-3 text-slate-300">
                    {row[h] !== null && row[h] !== undefined ? String(row[h]) : <span className="text-slate-600">NULL</span>}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};