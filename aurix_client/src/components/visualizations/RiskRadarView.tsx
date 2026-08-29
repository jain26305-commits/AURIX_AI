'use client';

import React from 'react';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { ShieldAlert } from 'lucide-react';

export const RiskRadarView: React.FC = () => {
  const auditFindings = [
    { id: 'AUD-801', type: '3-WAY MATCH', description: 'PO #4912 vs. GRN #891 vs. Invoice #INV-8812 Price Variance', variance: '$14,200', status: 'HELD FOR REVIEW' },
    { id: 'AUD-802', type: 'DUPLICATE INVOICE', description: 'Duplicate submission detected for Logistics Carrier APEX Freight', variance: '$24,000', status: 'BLOCKED' },
    { id: 'AUD-803', type: 'PHANTOM INVENTORY', description: 'Warehouse Sector B cycle count discrepancy on SKU-003', variance: '$8,400', status: 'ADJUSTMENT PENDING' },
  ];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <AurixCard
        title="VULNERABILITY PROPAGATION RADAR"
        subtitle="Multi-tier supply dependency stress testing"
        badge={<AurixBadge variant="gold">PHASE 26 RISK</AurixBadge>}
        className="lg:col-span-1"
      >
        <div className="h-56 flex flex-col items-center justify-center relative overflow-hidden bg-[#030303] rounded-lg border border-white/[0.05]">
          <div className="w-36 h-36 rounded-full border border-dashed border-[#D4AF37]/30 flex items-center justify-center animate-spin-slow">
            <div className="w-24 h-24 rounded-full border border-[#3DDB91]/40 flex items-center justify-center">
              <div className="w-12 h-12 rounded-full bg-[#D4AF37]/20 border border-[#D4AF37] flex items-center justify-center">
                <ShieldAlert className="w-5 h-5 text-[#D4AF37]" />
              </div>
            </div>
          </div>
          <span className="text-[10px] font-mono text-slate-400 mt-3">TIER-1 & TIER-2 TOPOLOGY SECURE</span>
        </div>
      </AurixCard>

      <AurixCard
        title="AUTONOMOUS ASSURANCE & LEAKAGE FINDINGS"
        subtitle="Continuous 3-way matching and discrepancy mitigation"
        badge={<AurixBadge variant="danger">$46.6K EXPOSURE</AurixBadge>}
        className="lg:col-span-2 space-y-3"
      >
        <div className="space-y-3 pt-2">
          {auditFindings.map((finding) => (
            <div
              key={finding.id}
              className="p-3.5 rounded-lg bg-white/[0.02] border border-white/[0.05] hover:border-[#D4AF37]/30 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-3 font-mono text-xs"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-[#D4AF37] font-bold">{finding.id}</span>
                  <AurixBadge variant="danger" size="sm">{finding.type}</AurixBadge>
                </div>
                <p className="text-white font-sans text-xs">{finding.description}</p>
              </div>

              <div className="text-right shrink-0">
                <span className="text-[10px] text-slate-500 uppercase block">FINANCIAL EXPOSURE</span>
                <span className="text-sm font-extrabold text-[#FF6B6B]">{finding.variance}</span>
              </div>
            </div>
          ))}
        </div>
      </AurixCard>
    </div>
  );
};
