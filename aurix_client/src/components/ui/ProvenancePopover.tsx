"use client";

import React, { useState } from "react";

export interface ProvenancePopoverProps {
  modelRef?: string;
  sourceDataset?: string;
  deterministicFormula?: string;
  lastVerifiedAt?: string;
}

export const ProvenancePopover: React.FC<ProvenancePopoverProps> = ({
  modelRef = "DETERMINISTIC_SOLVER_2.0",
  sourceDataset = "SAP_ERP_INVOICE_LEDGER",
  deterministicFormula = "Realized Value = Sum(Baseline Cost - Reallocated Cost)",
  lastVerifiedAt = "2026-08-23T05:00:00Z",
}) => {
  const [open, setOpen] = useState(false);

  return (
    <div className="relative inline-block text-left">
      <button
        onClick={() => setOpen(!open)}
        className="text-xs text-slate-500 hover:text-slate-300 transition flex items-center gap-1 font-mono"
        title="View Calculation Provenance"
      >
        <span>[?]</span>
        <span>Why?</span>
      </button>

      {open && (
        <div className="absolute right-0 z-50 mt-2 w-80 p-4 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl text-xs space-y-2">
          <div className="flex justify-between items-center border-b border-slate-800 pb-2">
            <span className="font-bold text-white uppercase tracking-wider">Provenance & Lineage</span>
            <button onClick={() => setOpen(false)} className="text-slate-400 hover:text-white">✕</button>
          </div>
          <div>
            <div className="text-slate-400 font-medium">Model / Engine:</div>
            <div className="font-mono text-slate-300">{modelRef}</div>
          </div>
          <div>
            <div className="text-slate-400 font-medium">Source Dataset:</div>
            <div className="font-mono text-slate-300">{sourceDataset}</div>
          </div>
          <div>
            <div className="text-slate-400 font-medium">Formula / Calculation:</div>
            <div className="p-2 bg-slate-950 rounded border border-slate-800 font-mono text-slate-300 text-[11px]">
              {deterministicFormula}
            </div>
          </div>
          <div className="text-[10px] text-slate-500 pt-1">
            Verified via PostgreSQL RLS at {lastVerifiedAt}
          </div>
        </div>
      )}
    </div>
  );
};
