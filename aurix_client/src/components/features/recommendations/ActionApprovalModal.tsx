'use client';

import React from 'react';
import { RecommendationItem } from '@/types/recommendation.types';
import { AurixButton } from '@/components/ui/AurixButton';

import { ShieldCheck, X, Check } from 'lucide-react';

interface ActionApprovalModalProps {
  item: RecommendationItem | null;
  isOpen: boolean;
  onClose: () => void;
  onConfirmApprove: (id: string) => void;
  isProcessing: boolean;
}

export const ActionApprovalModal: React.FC<ActionApprovalModalProps> = ({
  item,
  isOpen,
  onClose,
  onConfirmApprove,
  isProcessing,
}) => {
  if (!isOpen || !item) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md animate-pure-fade select-none">
      <div className="w-full max-w-lg aurix-card-glass bg-[#0C0E12] border border-gold/40 rounded-2xl p-6 shadow-2xl space-y-6 relative overflow-hidden">
        {/* Top Gold Accent */}
        <div className="absolute inset-x-0 top-0 h-[2px] bg-gradient-to-r from-transparent via-gold to-transparent" />

        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gold/10 border border-gold/30 flex items-center justify-center text-gold">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white tracking-wide">HUMAN-IN-THE-LOOP APPROVAL</h3>
              <p className="text-[11px] font-mono text-slate-400">Confirming execution sign-off for {item.id}</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white bg-white/[0.04] hover:bg-white/[0.08] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Prescription Summary */}
        <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06] text-xs font-mono space-y-3">
          <div>
            <span className="text-[10px] text-slate-500 uppercase font-bold block">TARGET PRESCRIPTION</span>
            <span className="text-white font-medium block mt-1">{item.prescriptiveAction}</span>
          </div>

          <div className="grid grid-cols-2 gap-3 pt-2 border-t border-white/[0.04]">
            <div>
              <span className="text-[10px] text-slate-500 block">COST TO EXECUTE:</span>
              <span className="text-white font-bold">₹{(item.costToExecuteINR / 1000).toFixed(0)}k</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-500 block">EXPOSURE AVOIDED:</span>
              <span className="text-gold font-bold">₹{(item.financialImpactAvoidedINR / 100000).toFixed(2)}L</span>
            </div>
          </div>
        </div>

        {/* Notice */}
        <p className="text-[11px] font-mono text-slate-400 leading-relaxed">
          Authorizing this recommendation logs a cryptographically verifiable execution token into the Phase 14 Decision Ledger and triggers downstream ERP purchase order workflows.
        </p>

        {/* Action Conduit */}
        <div className="flex items-center justify-end gap-3 pt-2">
          <AurixButton variant="ghost" size="sm" onClick={onClose} disabled={isProcessing}>
            CANCEL
          </AurixButton>
          <AurixButton
            variant="gold"
            size="md"
            loading={isProcessing}
            onClick={() => onConfirmApprove(item.id)}
          >
            <Check className="w-4 h-4 mr-1.5" />
            <span>CONFIRM & EXECUTE</span>
          </AurixButton>
        </div>
      </div>
    </div>
  );
};