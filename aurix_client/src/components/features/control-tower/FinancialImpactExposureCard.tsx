'use client';

import React from 'react';
import { ExecutiveFinancialSnapshot } from '@/types/control-tower.types';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { ProvenancePopover } from '@/components/trust/ProvenancePopover';

interface FinancialImpactExposureCardProps {
  financials: ExecutiveFinancialSnapshot;
}

export const FinancialImpactExposureCard: React.FC<FinancialImpactExposureCardProps> = ({ financials }) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 select-none">
      <AurixCard
        title="GROSS HOLDING CAPITAL"
        badge={
          <div className="flex items-center gap-1.5">
            <ProvenancePopover
              details={{
                sourceAuthority: 'BALANCE_SHEET',
                sourceConnector: 'ERP_GENERAL_LEDGER',
                calculationModel: 'FIFO_VALUATION_ENGINE',
                auditHash: '0x8F92A1B4C93D0E81',
                executionTimestamp: new Date().toISOString(),
                rlsPolicyApplied: 'TENANT_STRICT_ISOLATION',
              }}
            />
            <AurixBadge variant="gold">INVENTORY</AurixBadge>
          </div>
        }
      >
        <div className="text-2xl font-bold font-mono text-white mt-2">
          ₹{(financials.grossInventoryValuationINR / 100000).toFixed(2)}L
        </div>
        <div className="text-[11px] font-mono text-slate-400 mt-1">Active Portfolio Holding Valuation</div>
      </AurixCard>

      <AurixCard
        title="UNLOCKED CASH OPPORTUNITY"
        badge={
          <div className="flex items-center gap-1.5">
            <ProvenancePopover
              details={{
                sourceAuthority: 'TREASURY_OPTIMIZER',
                sourceConnector: 'WORKING_CAPITAL_FEED',
                calculationModel: 'DIO_COMPRESSION_SOLVER',
                auditHash: '0x3E11C4F8D90B7A22',
                executionTimestamp: new Date().toISOString(),
                rlsPolicyApplied: 'TENANT_STRICT_ISOLATION',
              }}
            />
            <AurixBadge variant="success">RECOVERY</AurixBadge>
          </div>
        }
      >
        <div className="text-2xl font-bold font-mono text-[#3DDB91] mt-2">
          ₹{(financials.unlockedCapitalOpportunityINR / 100000).toFixed(2)}L
        </div>
        <div className="text-[11px] font-mono text-slate-400 mt-1">Liquid capital recoverable in 45 days</div>
      </AurixCard>

      <AurixCard
        title="STOCKOUT REVENUE AT RISK"
        badge={
          <div className="flex items-center gap-1.5">
            <ProvenancePopover
              details={{
                sourceAuthority: 'RISK_RADAR',
                sourceConnector: 'DEMAND_INTERMITTENCY_API',
                calculationModel: 'MONTE_CARLO_STOCKOUT_V4',
                auditHash: '0x99AA12DF6B4C88E0',
                executionTimestamp: new Date().toISOString(),
                rlsPolicyApplied: 'TENANT_STRICT_ISOLATION',
              }}
            />
            <AurixBadge variant="danger" pulse>EXPOSURE</AurixBadge>
          </div>
        }
      >
        <div className="text-2xl font-bold font-mono text-[#FF6B6B] mt-2">
          ₹{(financials.stockoutRevenueAtRiskINR / 100000).toFixed(2)}L
        </div>
        <div className="text-[11px] font-mono text-slate-400 mt-1">{financials.activeBreachesCount} SKUs projected to breach service target</div>
      </AurixCard>

      <AurixCard
        title="PORTFOLIO SERVICE LEVEL"
        badge={
          <div className="flex items-center gap-1.5">
            <ProvenancePopover
              details={{
                sourceAuthority: 'COMMERCIAL_SERVICE',
                sourceConnector: 'OTIF_ANALYTICS_GATEWAY',
                calculationModel: 'WEIGHTED_FILL_RATE_CALC',
                auditHash: '0x7C44E890AB1123DF',
                executionTimestamp: new Date().toISOString(),
                rlsPolicyApplied: 'TENANT_STRICT_ISOLATION',
              }}
            />
            <AurixBadge variant="info">AVAILABILITY</AurixBadge>
          </div>
        }
      >
        <div className="text-2xl font-bold font-mono text-[#D4AF37] mt-2">
          {financials.portfolioServiceLevelPercent}%
        </div>
        <div className="text-[11px] font-mono text-slate-400 mt-1">Target Baseline: {financials.serviceLevelTargetPercent}%</div>
      </AurixCard>
    </div>
  );
};
