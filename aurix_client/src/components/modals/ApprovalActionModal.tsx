"use client";

import React, { useState } from "react";

export interface ApprovalActionModalProps {
  isOpen: boolean;
  onClose: () => void;
  approvalId: string;
  title: string;
  riskTier: string;
  blastRadiusExposureUsd: number;
  onDecision: (approvalId: string, approved: boolean, reason: string) => Promise<void>;
}

export const ApprovalActionModal: React.FC<ApprovalActionModalProps> = ({
  isOpen,
  onClose,
  approvalId,
  title,
  riskTier,
  blastRadiusExposureUsd,
  onDecision,
}) => {
  const [reason, setReason] = useState("");
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (approved: boolean) => {
    setLoading(true);
    try {
      await onDecision(approvalId, approved, reason);
      onClose();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="w-full max-w-lg bg-slate-900 border border-slate-700 rounded-2xl p-6 shadow-2xl space-y-5">
        <div className="flex justify-between items-start border-b border-slate-800 pb-3">
          <div>
            <span className="text-xs font-mono text-slate-400">APPROVAL TICKET {approvalId}</span>
            <h3 className="text-lg font-bold text-white mt-1">{title}</h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white">✕</button>
        </div>

        <div className="grid grid-cols-2 gap-3 p-4 bg-slate-950 border border-slate-800 rounded-xl text-xs font-mono">
          <div>
            <div className="text-slate-500">Risk Tier:</div>
            <div className="text-[#F3B33D] font-bold">{riskTier}</div>
          </div>
          <div>
            <div className="text-slate-500">Max Financial Blast:</div>
            <div className="text-white font-bold">${blastRadiusExposureUsd.toLocaleString()}</div>
          </div>
        </div>

        <div>
          <label className="text-xs text-slate-400">Approval Justification / Remarks</label>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="State rationale for audit ledger recording..."
            className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-gold h-20"
          />
        </div>

        <div className="flex gap-3 pt-2">
          <button
            disabled={loading}
            onClick={() => handleSubmit(false)}
            className="flex-1 py-2.5 bg-[#FF6B6B]/15 hover:bg-[#FF6B6B]/20 border border-[#FF6B6B]/40 text-[#FF6B6B] text-xs font-bold rounded-xl transition"
          >
            Reject Proposal
          </button>
          <button
            disabled={loading}
            onClick={() => handleSubmit(true)}
            className="flex-1 py-2.5 bg-[#3DDB91] hover:bg-[#3DDB91] text-white text-xs font-bold rounded-xl transition shadow-lg"
          >
            Authorize & Execute
          </button>
        </div>
      </div>
    </div>
  );
};
