'use client';

import React from 'react';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { Scale, CheckCircle2, AlertTriangle } from 'lucide-react';

interface ReconciliationRow {
  entity: string;
  sourceA: string;
  sourceB: string;
  recordsCompared: number;
  matchedRecords: number;
  discrepancies: number;
  matchRatePercent: number;
}

const RECONCILIATION_ROWS: ReconciliationRow[] = [
  { entity: 'Purchase Orders', sourceA: 'SAP S/4HANA', sourceB: 'Odoo Supply Chain', recordsCompared: 1420, matchedRecords: 1418, discrepancies: 2, matchRatePercent: 99.86 },
  { entity: 'Goods Receipts', sourceA: 'Odoo Supply Chain', sourceB: 'WMS Manhattan', recordsCompared: 2840, matchedRecords: 2835, discrepancies: 5, matchRatePercent: 99.82 },
  { entity: 'AP Invoices', sourceA: 'Tally Prime', sourceB: 'SAP S/4HANA', recordsCompared: 960, matchedRecords: 958, discrepancies: 2, matchRatePercent: 99.79 },
  { entity: 'Inventory On-Hand', sourceA: 'WMS Manhattan', sourceB: 'Tally Prime', recordsCompared: 412, matchedRecords: 411, discrepancies: 1, matchRatePercent: 99.76 },
  { entity: 'Freight Invoices', sourceA: 'Carrier EDI', sourceB: 'Tally Prime', recordsCompared: 184, matchedRecords: 184, discrepancies: 0, matchRatePercent: 100.0 },
];

export const ReconciliationMatrix: React.FC = () => {
  const totalCompared = RECONCILIATION_ROWS.reduce((sum, r) => sum + r.recordsCompared, 0);
  const totalDiscrepancies = RECONCILIATION_ROWS.reduce((sum, r) => sum + r.discrepancies, 0);
  const overallRate = ((totalCompared - totalDiscrepancies) / totalCompared) * 100;

  return (
    <AurixCard
      title="MULTI-SOURCE ERP RECONCILIATION"
      badge={<AurixBadge variant="success">{overallRate.toFixed(2)}% MATCH</AurixBadge>}
    >
      <div className="overflow-x-auto pt-2">
        <table className="w-full text-left text-xs font-mono">
          <thead>
            <tr className="text-slate-500 border-b border-white/[0.06] uppercase text-[10px] tracking-wider">
              <th className="py-2 pr-4 flex items-center gap-1.5"><Scale className="w-3 h-3" /> ENTITY</th>
              <th className="py-2 pr-4">SOURCE A</th>
              <th className="py-2 pr-4">SOURCE B</th>
              <th className="py-2 pr-4 text-right">COMPARED</th>
              <th className="py-2 pr-4 text-right">DISCREPANCIES</th>
              <th className="py-2 pr-4 text-right">MATCH RATE</th>
            </tr>
          </thead>
          <tbody>
            {RECONCILIATION_ROWS.map((row) => (
              <tr key={row.entity} className="border-b border-white/[0.03] hover:bg-white/[0.02]">
                <td className="py-2.5 pr-4 text-white font-bold">{row.entity}</td>
                <td className="py-2.5 pr-4 text-slate-300">{row.sourceA}</td>
                <td className="py-2.5 pr-4 text-slate-300">{row.sourceB}</td>
                <td className="py-2.5 pr-4 text-right text-slate-300">{row.recordsCompared.toLocaleString()}</td>
                <td className="py-2.5 pr-4 text-right">
                  {row.discrepancies === 0 ? (
                    <span className="text-[#3DDB91] inline-flex items-center gap-1 justify-end">
                      <CheckCircle2 className="w-3 h-3" /> 0
                    </span>
                  ) : (
                    <span className="text-[#F3B33D] inline-flex items-center gap-1 justify-end">
                      <AlertTriangle className="w-3 h-3" /> {row.discrepancies}
                    </span>
                  )}
                </td>
                <td className="py-2.5 pr-4 text-right text-white font-bold">{row.matchRatePercent.toFixed(2)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-[11px] text-slate-500 font-sans leading-relaxed pt-4 mt-2 border-t border-white/[0.05]">
        Reconciliation runs nightly across canonical entity keys, adjudicating field-level discrepancies
        via deterministic matching first, then probabilistic entity resolution for near-matches. Unresolved
        discrepancies route to the Data Quality workspace for manual review.
      </p>
    </AurixCard>
  );
};
