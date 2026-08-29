'use client';

import React from 'react';
import { AtpInquiryResponse } from '@/types/fulfillment.types';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { AurixButton } from '@/components/ui/AurixButton';
import { Calculator, AlertOctagon } from 'lucide-react';

interface AtpInquiryCardProps {
  skuId: string;
  onSkuChange: (id: string) => void;
  units: number;
  onUnitsChange: (units: number) => void;
  onCheckAtp: () => void;
  result: AtpInquiryResponse | null;
  loading: boolean;
}

export const AtpInquiryCard: React.FC<AtpInquiryCardProps> = ({
  skuId,
  onSkuChange,
  units,
  onUnitsChange,
  onCheckAtp,
  result,
  loading,
}) => {
  return (
    <AurixCard
      title="DYNAMIC AVAILABLE-TO-PROMISE (ATP / CTP) PROMISSORY ENGINE"
      badge={<AurixBadge variant="gold">DETERMINISTIC PROMISSING</AurixBadge>}
    >
      <div className="space-y-6 text-xs font-mono select-none">
        {/* Input Parameters */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pb-4 border-b border-white/[0.06]">
          <div className="space-y-1">
            <label className="text-slate-400 text-[10px] uppercase font-bold">MATERIAL SKU</label>
            <select
              value={skuId}
              onChange={(e) => onSkuChange(e.target.value)}
              className="w-full bg-[#15171A] border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none"
            >
              <option value="SKU-001">SKU-001 — 101 Beige-L (T-Shirt)</option>
              <option value="SKU-002">SKU-002 — 101 Beige-M (T-Shirt)</option>
              <option value="SKU-003">SKU-003 — 102 Navy-L (Polo)</option>
              <option value="SKU-004">SKU-004 — 103 Black-XXL (Hoodie)</option>
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-slate-400 text-[10px] uppercase font-bold">REQUESTED ORDER QUANTITY</label>
            <input
              type="number"
              min="1"
              max="5000"
              value={units}
              onChange={(e) => onUnitsChange(Number(e.target.value))}
              className="w-full bg-[#15171A] border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none"
            />
          </div>

          <div className="flex items-end">
            <AurixButton variant="gold" size="md" className="w-full" onClick={onCheckAtp} loading={loading}>
              <Calculator className="w-4 h-4 mr-1.5" />
              <span>RUN ATP/CTP EVALUATION</span>
            </AurixButton>
          </div>
        </div>

        {/* Evaluation Output */}
        {result && (
          <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06] space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-white font-bold text-sm block">{result.skuName}</span>
                <span className="text-[10px] text-slate-500">Inquiry for {result.requestedUnits} units</span>
              </div>

              <AurixBadge variant={result.canFulfillImmediately ? 'success' : 'warning'} pulse={!result.canFulfillImmediately}>
                {result.canFulfillImmediately ? 'IMMEDIATE FULFILLMENT' : 'CAPABLE TO PROMISE (CTP)'}
              </AurixBadge>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center pt-2">
              <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                <span className="text-[9px] text-slate-500 uppercase block">ATP (UNCOMMITTED)</span>
                <span className="text-base font-bold text-white mt-0.5 block">{result.availableToPromiseUnits} pcs</span>
              </div>

              <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                <span className="text-[9px] text-slate-500 uppercase block">CTP (RECEIPTS INCL.)</span>
                <span className="text-base font-bold text-[#D4AF37] mt-0.5 block">{result.capableToPromiseUnits} pcs</span>
              </div>

              <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                <span className="text-[9px] text-slate-500 uppercase block">PROMISED DELIVERY</span>
                <span className="text-base font-bold text-gold mt-0.5 block">{result.promisedDeliveryDate}</span>
              </div>

              <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                <span className="text-[9px] text-slate-500 uppercase block">LEAD TIME REQUIRED</span>
                <span className="text-base font-bold text-white mt-0.5 block">{result.leadTimeDaysRequired} Days</span>
              </div>
            </div>

            {result.constrainingFactor && (
              <div className="p-3 rounded-lg bg-[#FF6B6B]/10 border border-[#FF6B6B]/25 text-[11px] text-[#FF8585] flex items-start gap-2">
                <AlertOctagon className="w-4 h-4 shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold block">FULFILLMENT CONSTRAINT DETECTED:</span>
                  {result.constrainingFactor}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </AurixCard>
  );
};