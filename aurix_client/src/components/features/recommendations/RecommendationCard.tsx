'use client';

import React from 'react';
import { RecommendationItem } from '@/types/recommendation.types';

import { AurixBadge } from '@/components/ui/AurixBadge';
import { AurixButton } from '@/components/ui/AurixButton';
import { AlertOctagon, HelpCircle, CheckCircle2, XCircle, ShieldCheck, Cpu } from 'lucide-react';

interface RecommendationCardProps {
  item: RecommendationItem;
  onOpenApproval: () => void;
  onOpenProvenance: () => void;
  onReject: () => void;
  onSimulate: () => void;
}

export const RecommendationCard: React.FC<RecommendationCardProps> = ({
  item,
  onOpenApproval,
  onOpenProvenance,
  onReject,
  onSimulate,
}) => {
  const isCritical = item.severity === 'CRITICAL';
  const isApproved = item.status === 'APPROVED';
  const isRejected = item.status === 'REJECTED';

  return (
    <div
      className={`aurix-card-glass rounded-xl p-6 border transition-all duration-300 relative overflow-hidden space-y-6 select-none ${
        isCritical
          ? 'border-[#FF6B6B]/40 shadow-[0_0_30px_rgba(255,107,107,0.1)]'
          : 'border-white/[0.08] hover:border-white/20'
      }`}
    >
      {/* Top Laser Accent */}
      <div
        className={`absolute inset-x-0 top-0 h-[2px] ${
          isCritical ? 'bg-gradient-to-r from-transparent via-[#FF6B6B] to-transparent' : 'bg-gradient-to-r from-transparent via-gold to-transparent'
        }`}
      />

      {/* Header Block */}
      <div className="flex flex-wrap items-start justify-between gap-4 pb-4 border-b border-white/[0.06]">
        <div className="space-y-1">
          <div className="flex items-center gap-2.5">
            <AurixBadge
              variant={isCritical ? 'danger' : item.severity === 'HIGH' ? 'warning' : 'info'}
              pulse={isCritical}
            >
              {item.severity} SIGNAL
            </AurixBadge>
            <span className="text-[10px] font-mono text-slate-500">{item.id}</span>
            {item.targetSkuId && (
              <span className="px-2 py-0.5 rounded bg-white/[0.04] border border-white/10 text-gold text-[10px] font-mono font-bold">
                {item.targetSkuId}
              </span>
            )}
          </div>
          <h3 className="text-base font-bold text-white tracking-wide">{item.title}</h3>
        </div>

        {/* Confidence & DQ Badge Ribbon */}
        <div className="flex items-center gap-3 font-mono text-xs">
          <div className="text-right">
            <span className="text-[9px] text-slate-500 uppercase block">MODEL CONFIDENCE</span>
            <span className="text-sm font-bold text-[#3DDB91]">{item.confidencePercent}%</span>
          </div>
          <div className="h-6 w-px bg-white/10" />
          <div className="text-right">
            <span className="text-[9px] text-slate-500 uppercase block">DATA QUALITY</span>
            <span className="text-sm font-bold text-[#D4AF37]">{item.dataQualityScore}%</span>
          </div>
        </div>
      </div>

      {/* 6-Question Structured Advisor Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
        {/* Q1 & Q2: WHAT HAPPENED & WHY */}
        <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.04] space-y-3">
          <div>
            <span className="text-[10px] text-slate-500 uppercase font-bold flex items-center gap-1.5 text-[#FF8585]">
              <AlertOctagon className="w-3.5 h-3.5" /> 1. WHAT HAPPENED?
            </span>
            <p className="text-slate-300 mt-1 leading-relaxed">{item.whatHappened}</p>
          </div>

          <div className="pt-2 border-t border-white/[0.04]">
            <span className="text-[10px] text-slate-500 uppercase font-bold flex items-center gap-1.5 text-gold">
              <Cpu className="w-3.5 h-3.5" /> 2. ROOT CAUSE ATTRIBUTION
            </span>
            <p className="text-slate-300 mt-1 leading-relaxed">{item.rootCause}</p>
          </div>
        </div>

        {/* Q3 & Q4: PRESCRIPTION & IMPACT */}
        <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.04] space-y-3">
          <div>
            <span className="text-[10px] text-slate-500 uppercase font-bold flex items-center gap-1.5 text-[#3DDB91]">
              <ShieldCheck className="w-3.5 h-3.5" /> 3. PRESCRIPTIVE ACTION
            </span>
            <p className="text-white font-medium mt-1 leading-relaxed">{item.prescriptiveAction}</p>
          </div>

          <div className="pt-2 border-t border-white/[0.04] flex items-center justify-between text-[11px]">
            <div>
              <span className="text-slate-500 block text-[9px]">EXPECTED SERVICE RESTORED</span>
              <span className="text-[#3DDB91] font-bold">{item.expectedServiceLevelRestoredPercent}%</span>
            </div>
            <div className="text-right">
              <span className="text-slate-500 block text-[9px]">COST OF INACTION</span>
              <span className="text-[#FF6B6B] font-bold">₹{(item.costOfInactionINR / 100000).toFixed(2)}L</span>
            </div>
          </div>
        </div>
      </div>

      {/* Financial ROI Conduit Ribbon */}
      <div className="p-3.5 rounded-xl bg-gold/[0.05] border border-gold/20 flex flex-wrap items-center justify-between gap-4 text-xs font-mono">
        <div className="flex items-center gap-6">
          <div>
            <span className="text-[9px] text-slate-500 uppercase block">EXECUTION COST</span>
            <span className="text-white font-bold">₹{(item.costToExecuteINR / 1000).toFixed(0)}k</span>
          </div>
          <div className="h-4 w-px bg-white/10" />
          <div>
            <span className="text-[9px] text-slate-500 uppercase block">EXPOSURE AVOIDED</span>
            <span className="text-gold font-bold">₹{(item.financialImpactAvoidedINR / 100000).toFixed(2)}L</span>
          </div>
        </div>

        <button
          onClick={onOpenProvenance}
          className="text-slate-400 hover:text-white flex items-center gap-1 text-[11px] underline underline-offset-4 cursor-pointer"
        >
          <HelpCircle className="w-3.5 h-3.5 text-gold" />
          <span>INSPECT MATHEMATICAL PROVENANCE</span>
        </button>
      </div>

      {/* Governance & Human-in-the-Loop Action Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="text-slate-500">GOVERNANCE STATE:</span>
          {isApproved && <AurixBadge variant="success">APPROVED & DISPATCHED</AurixBadge>}
          {isRejected && <AurixBadge variant="danger">REJECTED BY OPERATOR</AurixBadge>}
          {item.status === 'PENDING_REVIEW' && (
            <AurixBadge variant="warning">AWAITING HUMAN APPROVAL</AurixBadge>
          )}
        </div>

        <div className="flex items-center gap-3">
          <AurixButton variant="ghost" size="sm" onClick={onSimulate}>
            <span>SIMULATE WHAT-IF</span>
          </AurixButton>

          {item.status === 'PENDING_REVIEW' && (
            <>
              <AurixButton variant="secondary" size="sm" onClick={onReject}>
                <XCircle className="w-3.5 h-3.5 mr-1" />
                <span>REJECT</span>
              </AurixButton>
              <AurixButton variant="gold" size="sm" onClick={onOpenApproval}>
                <CheckCircle2 className="w-3.5 h-3.5 mr-1.5" />
                <span>APPROVE ACTION</span>
              </AurixButton>
            </>
          )}
        </div>
      </div>
    </div>
  );
};