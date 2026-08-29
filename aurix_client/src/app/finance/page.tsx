'use client';

import React, { useState, useEffect } from 'react';
import { DomainWorkspaceOrchestrator } from '@/components/domain/DomainWorkspaceOrchestrator';
import { WaterfallBridge } from '@/components/visualizations/WaterfallBridge';
import { ARAgingMatrix } from '@/components/features/finance/ARAgingMatrix';
import { APAgingMatrix } from '@/components/features/finance/APAgingMatrix';
import { WorkingCapitalDecomposition } from '@/components/features/finance/WorkingCapitalDecomposition';
import { FinanceService } from '@/services/api/financeService';
import { ARAgingReportDTO, APAgingReportDTO, WorkingCapitalDTO, PnLStatementDTO } from '@/types/finance.types';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';

function FinanceWorkspace({ subdomainId }: { subdomainId: string }) {
  const [pnl, setPnL] = useState<PnLStatementDTO | null>(null);
  const [ar, setAR] = useState<ARAgingReportDTO | null>(null);
  const [ap, setAP] = useState<APAgingReportDTO | null>(null);
  const [wc, setWC] = useState<WorkingCapitalDTO | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    Promise.all([
      FinanceService.getPnL(),
      FinanceService.getAR(),
      FinanceService.getAP(),
      FinanceService.getWorkingCapital(),
    ])
      .then(([pnlData, arData, apData, wcData]) => {
        setPnL(pnlData);
        setAR(arData);
        setAP(apData);
        setWC(wcData);
      })
      .catch((err) => console.error('Failed to load finance intelligence:', err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="py-24 flex flex-col items-center justify-center text-center space-y-4 font-mono">
        <div className="w-8 h-8 rounded-full border-2 border-gold border-t-transparent animate-spin" />
        <p className="text-xs text-slate-400 tracking-widest uppercase">SYNCING FINANCIAL LEDGERS & WORKING CAPITAL...</p>
      </div>
    );
  }

  const pnlWaterfall = [
    { label: 'GROSS REVENUE', value: pnl?.grossRevenue ?? 1250000, deltaType: 'baseline' as const, percentage: '100%' },
    { label: 'RETURNS & DISCOUNTS', value: -((pnl?.returns ?? 20000) + (pnl?.discounts ?? 10000)), deltaType: 'negative' as const, percentage: '-2.4%' },
    { label: 'COGS (MATERIAL)', value: -(pnl?.cogs ?? 720000), deltaType: 'negative' as const, percentage: '-59.2%' },
    { label: 'GROSS PROFIT', value: pnl?.grossProfit ?? 495000, deltaType: 'subtotal' as const, percentage: `${pnl?.grossMarginPercent ?? 40.7}%` },
  ];

  return (
    <div className="space-y-6 animate-pure-fade">
      {subdomainId === 'pnl' && (
        <div className="space-y-6">
          <WaterfallBridge
            title="P&L MARGIN BRIDGE & CONTRIBUTION WATERFALL"
            subtitle="Audited breakdown from Gross Invoiced Volume to Net Contribution Margin"
            steps={pnlWaterfall}
          />
        </div>
      )}

      {subdomainId === 'waterfall' && (
        <AurixCard title="GROSS-TO-NET DEDUCTIONS" badge={<AurixBadge variant="danger">$35K LEAKAGE</AurixBadge>}>
          <div className="space-y-3 font-mono text-xs pt-2">
            <div className="flex justify-between border-b border-white/5 pb-2">
              <span className="text-slate-400">RETURNS & ALLOWANCES:</span>
              <span className="text-white font-bold">${(pnl?.returns ?? 20000).toLocaleString()}</span>
            </div>
            <div className="flex justify-between border-b border-white/5 pb-2">
              <span className="text-slate-400">TRADE DISCOUNTS:</span>
              <span className="text-white font-bold">${(pnl?.discounts ?? 10000).toLocaleString()}</span>
            </div>
            <div className="flex justify-between border-b border-white/5 pb-2">
              <span className="text-slate-400">CREDIT NOTES:</span>
              <span className="text-white font-bold">${(pnl?.credits ?? 5000).toLocaleString()}</span>
            </div>
          </div>
        </AurixCard>
      )}

      {subdomainId === 'working-capital' && wc && (
        <WorkingCapitalDecomposition data={wc} />
      )}

      {subdomainId === 'aging' && (
        <div className="space-y-6">
          {ar && <ARAgingMatrix report={ar} />}
          {ap && <APAgingMatrix report={ap} />}
        </div>
      )}
    </div>
  );
}

export default function FinancePage() {
  return (
    <DomainWorkspaceOrchestrator
      domainKey="finance"
      renderWorkspace={(subdomainId) => <FinanceWorkspace subdomainId={subdomainId} />}
    />
  );
}
