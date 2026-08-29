'use client';

import React, { useState } from 'react';
import { ShieldCheck, X } from 'lucide-react';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';

export interface ProvenanceDetails {
  sourceAuthority: string;
  sourceConnector: string;
  calculationModel: string;
  auditHash: string;
  executionTimestamp: string;
  rlsPolicyApplied: string;
}

export interface ProvenancePopoverProps {
  details: ProvenanceDetails;
  children?: React.ReactNode;
}

export const ProvenancePopover: React.FC<ProvenancePopoverProps> = ({
  details,
  children,
}) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative inline-block">
      <button
        type="button"
        onClick={() => setIsOpen((open) => !open)}
        className={
          children
            ? 'inline-flex items-center cursor-pointer'
            : 'inline-flex items-center gap-1 font-mono text-[9px] text-slate-500 hover:text-[#D4AF37] transition-colors bg-white/[0.02] px-1.5 py-0.5 rounded border border-white/[0.04] cursor-pointer'
        }
        title="View Lineage & Audit Provenance"
        aria-expanded={isOpen}
        aria-haspopup="dialog"
      >
        {children ?? (
          <>
            <ShieldCheck className="w-3 h-3 text-[#3DDB91]" />
            <span>{details.sourceAuthority}</span>
          </>
        )}
      </button>

      {isOpen && (
        <div
          className="absolute right-0 top-full mt-2 w-80 z-50 animate-pure-fade shadow-2xl"
          role="dialog"
          aria-label="Audit and provenance details"
        >
          <AurixCard
            title="AUDIT & PROVENANCE"
            badge={<AurixBadge variant="gold">VERIFIED</AurixBadge>}
            action={
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="text-slate-400 hover:text-white p-1"
                aria-label="Close provenance details"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            }
            className="p-4 border-[#D4AF37]/30 bg-[#07090D] shadow-[0_12px_40px_rgba(0,0,0,0.9)]"
          >
            <div className="space-y-2 font-mono text-[10px] pt-1">
              <div className="flex justify-between border-b border-white/[0.04] pb-1.5">
                <span className="text-slate-500">AUTHORITY:</span>
                <span className="text-white font-bold">
                  {details.sourceAuthority}
                </span>
              </div>

              <div className="flex justify-between border-b border-white/[0.04] pb-1.5">
                <span className="text-slate-500">CONNECTOR:</span>
                <span className="text-slate-300">
                  {details.sourceConnector}
                </span>
              </div>

              <div className="flex justify-between border-b border-white/[0.04] pb-1.5">
                <span className="text-slate-500">ML MODEL:</span>
                <span className="text-[#D4AF37] font-bold">
                  {details.calculationModel}
                </span>
              </div>

              <div className="flex justify-between border-b border-white/[0.04] pb-1.5">
                <span className="text-slate-500">RLS POLICY:</span>
                <span className="text-[#3DDB91] font-bold">
                  {details.rlsPolicyApplied}
                </span>
              </div>

              <div className="pt-1">
                <span className="text-[9px] text-slate-500 block mb-0.5">
                  CRYPTOGRAPHIC HASH:
                </span>

                <span className="text-[9px] text-[#D4AF37] font-mono break-all block bg-white/[0.02] p-1 rounded border border-white/[0.04]">
                  {details.auditHash}
                </span>
              </div>
            </div>
          </AurixCard>
        </div>
      )}
    </div>
  );
};