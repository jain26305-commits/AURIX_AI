'use client';

import React from 'react';
import { Phase14ActionItem } from '@/types/action.types';
import { AurixButton } from '@/components/ui/AurixButton';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { X, ShieldCheck, CheckCircle2, XCircle } from 'lucide-react';
import { formatINR } from '@/lib/formatters';

interface PreflightCheckDrawerProps {
  action: Phase14ActionItem | null;
  isOpen: boolean;
  onClose: () => void;
  onApprove: (id: string) => void;
  onReject: (id: string, reason: string) => void;
  isProcessing: boolean;
}

export const PreflightCheckDrawer: React.FC<PreflightCheckDrawerProps> = ({
  action,
  isOpen,
  onClose,
  onApprove,
  onReject,
  isProcessing,
}) => {
  if (!isOpen || !action) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm animate-pure-fade select-none font-mono">
      <div className="w-full max-w-xl bg-[#0C0E12] border-l border-white/10 h-full p-6 overflow-y-auto space-y-6">
        {/* Drawer Header */}
        <div className="flex items-center justify-between pb-4 border-b border-white/10">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-gold" />
              PHASE 14 PREFLIGHT GATEWAY
            </h3>
            <span className="text-xs text-slate-400">Deterministic validation for {action.id}</span>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg bg-white/[0.05] hover:bg-white/10 text-slate-400 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Action Payload Summary */}
        <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06] space-y-2.5 text-xs">
          <div className="flex justify-between">
            <span className="text-slate-500">PRESCRIPTION:</span>
            <span className="text-white font-bold">{action.title}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">COMMITMENT:</span>
            <span className="text-white font-bold">{formatINR(action.prescriptivePayload.financialCommitmentINR)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">ESTIMATED REVENUE RECOVERY:</span>
            <span className="text-[#3DDB91] font-bold">{formatINR(action.prescriptivePayload.expectedRoiINR)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">REQUIRED SIGN-OFF ROLE:</span>
            <span className="text-gold font-bold">{action.assignedApproverRole}</span>
          </div>
        </div>

        {/* Preflight Checks Matrix */}
        <div className="space-y-3">
          <span className="text-[10px] text-gold uppercase tracking-widest font-bold block">
            DETERMINISTIC VALIDATION CRITERIA
          </span>

          <div className="space-y-2">
            {action.preflightChecks.map((chk) => (
              <div
                key={chk.checkId}
                className="p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.06] space-y-1 text-xs"
              >
                <div className="flex items-center justify-between">
                  <span className="text-white font-bold flex items-center gap-1.5">
                    {chk.passed ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-[#3DDB91]" />
                    ) : (
                      <XCircle className="w-3.5 h-3.5 text-[#FF6B6B]" />
                    )}
                    {chk.name}
                  </span>
                  <AurixBadge variant={chk.passed ? 'success' : 'danger'}>
                    {chk.category}
                  </AurixBadge>
                </div>
                <p className="text-slate-400 text-[11px] leading-relaxed pl-5">{chk.message}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Action Conduit */}
        {action.state === 'AWAITING_APPROVAL' && (
          <div className="pt-4 border-t border-white/10 flex items-center justify-end gap-3">
            <AurixButton
              variant="secondary"
              size="md"
              onClick={() => onReject(action.id, 'Rejected by operator.')}
              disabled={isProcessing}
            >
              REJECT ACTION
            </AurixButton>
            <AurixButton
              variant="gold"
              size="md"
              onClick={() => onApprove(action.id)}
              loading={isProcessing}
            >
              <ShieldCheck className="w-4 h-4 mr-1.5" />
              <span>APPROVE & ISSUE TOKEN</span>
            </AurixButton>
          </div>
        )}
      </div>
    </div>
  );
};