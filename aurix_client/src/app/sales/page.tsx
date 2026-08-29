'use client';

import React from 'react';
import { DomainWorkspaceOrchestrator } from '@/components/domain/DomainWorkspaceOrchestrator';
import { useSalesIntelligence } from '@/hooks/useSalesIntelligence';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { TrendingUp, Users, DollarSign, ShieldAlert } from 'lucide-react';

function SalesWorkspace({ subdomainId }: { subdomainId: string }) {
  const { data, loading } = useSalesIntelligence();

  if (loading || !data) {
    return (
      <div className="py-24 flex flex-col items-center justify-center text-center space-y-4 font-mono">
        <div className="w-8 h-8 rounded-full border-2 border-gold border-t-transparent animate-spin" />
        <p className="text-xs text-slate-400 tracking-widest uppercase">LOADING COMMERCIAL INTELLIGENCE & O2C TELEMETRY...</p>
      </div>
    );
  }

  const { summary, pvmBreakdown, customers, concentration, o2cRisks, opportunities } = data;

  return (
    <div className="space-y-6">
      {/* EXECUTIVE COMMERCIAL PULSE STATS BAR */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <AurixCard title="GROSS REVENUE (YTD)" badge={<AurixBadge variant="gold">COMMERCIAL</AurixBadge>}>
          <div className="flex items-baseline justify-between mt-2">
            <span className="text-2xl font-bold text-white">₹{(summary.grossRevenueINR / 10000000).toFixed(2)}Cr</span>
            <TrendingUp className="w-5 h-5 text-gold" />
          </div>
          <div className="text-[11px] text-slate-400 mt-1">
            <span className="text-[#3DDB91] font-bold">+{summary.revenueGrowthPercent}%</span> vs prior period ({summary.revenueVsPlanPercent}% of plan)
          </div>
        </AurixCard>

        <AurixCard title="CONTRIBUTION MARGIN" badge={<AurixBadge variant="success">PROFITABILITY</AurixBadge>}>
          <div className="flex items-baseline justify-between mt-2">
            <span className="text-2xl font-bold text-[#3DDB91]">{summary.contributionMarginPercent}%</span>
            <DollarSign className="w-5 h-5 text-[#3DDB91]" />
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Gross Margin: {summary.grossMarginPercent}% | ASP: ₹{summary.averageSellingPriceINR}</div>
        </AurixCard>

        <AurixCard title="ACTIVE ACCOUNTS" badge={<AurixBadge variant="gold">CUSTOMER 360</AurixBadge>}>
          <div className="flex items-baseline justify-between mt-2">
            <span className="text-2xl font-bold text-white">{summary.activeCustomersCount}</span>
            <Users className="w-5 h-5 text-gold" />
          </div>
          <div className="text-[11px] text-slate-400 mt-1">+{summary.newCustomersCount} new | -{summary.churnedCustomersCount} churned</div>
        </AurixCard>

        <AurixCard title="REVENUE AT RISK" badge={<AurixBadge variant="danger" pulse>EXPOSURE</AurixBadge>}>
          <div className="flex items-baseline justify-between mt-2">
            <span className="text-2xl font-bold text-[#FF6B6B]">₹{(summary.revenueAtRiskINR / 100000).toFixed(1)}L</span>
            <ShieldAlert className="w-5 h-5 text-[#FF6B6B]" />
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Lost sales: ₹{(summary.lostSalesValueINR / 100000).toFixed(1)}L</div>
        </AurixCard>
      </div>

      {/* OVERVIEW SUBDOMAIN */}
      {subdomainId === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-pure-fade">
          <AurixCard title="PRICE-VOLUME-MIX (PVM) VARIANCE" badge={<AurixBadge variant="gold">DECOMPOSITION</AurixBadge>}>
            <div className="space-y-4 pt-2 font-mono text-xs">
              {pvmBreakdown.map((item) => (
                <div key={item.dimension} className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.05] space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-white font-bold">{item.dimension}</span>
                    <span className="text-[#3DDB91] font-bold">+₹{(item.netVarianceINR / 100000).toFixed(1)}L</span>
                  </div>
                  <div className="grid grid-cols-3 gap-2 pt-1 text-[11px]">
                    <div>
                      <span className="text-slate-500 block">PRICE EFFECT</span>
                      <span className={item.priceEffectINR >= 0 ? 'text-[#3DDB91]' : 'text-[#FF6B6B]'}>
                        ₹{(item.priceEffectINR / 1000).toFixed(0)}k
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-500 block">VOLUME EFFECT</span>
                      <span className={item.volumeEffectINR >= 0 ? 'text-[#3DDB91]' : 'text-[#FF6B6B]'}>
                        ₹{(item.volumeEffectINR / 1000).toFixed(0)}k
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-500 block">MIX EFFECT</span>
                      <span className={item.mixEffectINR >= 0 ? 'text-[#3DDB91]' : 'text-[#FF6B6B]'}>
                        ₹{(item.mixEffectINR / 1000).toFixed(0)}k
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </AurixCard>

          <AurixCard title="TOP COMMERCIAL OPPORTUNITIES" badge={<AurixBadge variant="success">PIPELINE</AurixBadge>}>
            <div className="space-y-3 pt-2 font-mono text-xs">
              {opportunities.map((opp) => (
                <div key={opp.opportunityId} className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.05] space-y-1">
                  <div className="flex justify-between items-center">
                    <span className="text-gold font-bold">{opp.customerName} ({opp.opportunityType})</span>
                    <span className="text-white font-bold">₹{(opp.estimatedValueINR / 100000).toFixed(1)}L</span>
                  </div>
                  <p className="text-slate-300 font-sans text-[11px]">{opp.description}</p>
                  <p className="text-slate-400 font-sans text-[10px] pt-1">Action: {opp.suggestedAction}</p>
                </div>
              ))}
            </div>
          </AurixCard>
        </div>
      )}

      {/* REVENUE & PVM SUBDOMAIN */}
      {subdomainId === 'pvm' && (
        <div className="space-y-6 animate-pure-fade">
          <AurixCard title="DETAILED PVM VARIANCE BRIDGE" badge={<AurixBadge variant="gold">ANALYTICAL BRIDGE</AurixBadge>}>
            <div className="overflow-x-auto">
              <table className="w-full text-left font-mono text-xs">
                <thead>
                  <tr className="border-b border-white/10 text-slate-400">
                    <th className="pb-3 font-medium">DIMENSION / PRODUCT LINE</th>
                    <th className="pb-3 font-medium text-right">BASELINE (INR)</th>
                    <th className="pb-3 font-medium text-right">CURRENT (INR)</th>
                    <th className="pb-3 font-medium text-right">PRICE EFFECT</th>
                    <th className="pb-3 font-medium text-right">VOLUME EFFECT</th>
                    <th className="pb-3 font-medium text-right">MIX EFFECT</th>
                    <th className="pb-3 font-medium text-right">NET VARIANCE</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5 text-slate-300">
                  {pvmBreakdown.map((row) => (
                    <tr key={row.dimension} className="hover:bg-white/[0.02]">
                      <td className="py-3 text-white font-medium">{row.dimension}</td>
                      <td className="py-3 text-right">₹{row.baselineRevenueINR.toLocaleString()}</td>
                      <td className="py-3 text-right">₹{row.currentRevenueINR.toLocaleString()}</td>
                      <td className="py-3 text-right text-[#3DDB91]">₹{row.priceEffectINR.toLocaleString()}</td>
                      <td className="py-3 text-right text-[#3DDB91]">₹{row.volumeEffectINR.toLocaleString()}</td>
                      <td className="py-3 text-right text-[#3DDB91]">₹{row.mixEffectINR.toLocaleString()}</td>
                      <td className="py-3 text-right text-gold font-bold">₹{row.netVarianceINR.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </AurixCard>
        </div>
      )}

      {/* CUSTOMERS 360 SUBDOMAIN */}
      {subdomainId === 'customers' && (
        <div className="space-y-6 animate-pure-fade">
          <AurixCard title="CUSTOMER 360 ENTERPRISE ACCOUNTS" badge={<AurixBadge variant="gold">ACCOUNT INTELLIGENCE</AurixBadge>}>
            <div className="overflow-x-auto">
              <table className="w-full text-left font-mono text-xs">
                <thead>
                  <tr className="border-b border-white/10 text-slate-400">
                    <th className="pb-3 font-medium">CUSTOMER NAME</th>
                    <th className="pb-3 font-medium">TIER / SEGMENT</th>
                    <th className="pb-3 font-medium text-right">REVENUE (INR)</th>
                    <th className="pb-3 font-medium text-right">MARGIN %</th>
                    <th className="pb-3 font-medium text-right">ORDERS</th>
                    <th className="pb-3 font-medium text-right">GROWTH</th>
                    <th className="pb-3 font-medium text-center">RISK</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5 text-slate-300">
                  {customers.map((cust) => (
                    <tr key={cust.customerId} className="hover:bg-white/[0.02]">
                      <td className="py-3 text-white font-bold">{cust.customerName}</td>
                      <td className="py-3">
                        <span className="text-slate-400">{cust.tier}</span>
                        <span className="text-slate-500 block text-[10px]">{cust.segment}</span>
                      </td>
                      <td className="py-3 text-right font-medium">₹{cust.revenueINR.toLocaleString()}</td>
                      <td className="py-3 text-right text-[#3DDB91]">{cust.marginPercent}%</td>
                      <td className="py-3 text-right">{cust.ordersCount}</td>
                      <td className="py-3 text-right text-[#3DDB91]">+{cust.growthPercent}%</td>
                      <td className="py-3 text-center">
                        <AurixBadge variant={cust.segmentRisk === 'CRITICAL' ? 'danger' : cust.segmentRisk === 'MODERATE' ? 'warning' : 'success'}>
                          {cust.segmentRisk}
                        </AurixBadge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </AurixCard>
        </div>
      )}

      {/* CUSTOMER CONCENTRATION SUBDOMAIN */}
      {subdomainId === 'concentration' && (
        <div className="space-y-6 animate-pure-fade">
          <AurixCard title="CUSTOMER CONCENTRATION & PARETO ANALYSIS" badge={<AurixBadge variant="warning">HHI EXPOSURE</AurixBadge>}>
            <div className="space-y-4 pt-2 font-mono text-xs">
              {concentration.map((tier) => (
                <div key={tier.tierName} className="p-4 rounded-lg bg-white/[0.02] border border-white/[0.05] space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-white font-bold">{tier.tierName} ({tier.customerCount} accounts)</span>
                    <span className="text-gold font-bold">₹{(tier.revenueINR / 100000).toFixed(1)}L ({tier.revenueSharePercent}%)</span>
                  </div>
                  <div className="h-2 rounded-full bg-white/5 overflow-hidden">
                    <div className="h-full bg-gold rounded-full" style={{ width: `${tier.revenueSharePercent}%` }} />
                  </div>
                  <div className="flex justify-between text-[11px] text-slate-400 pt-1">
                    <span>Cumulative Share: {tier.cumulativeSharePercent}%</span>
                    <span>HHI Contribution: {tier.hhiContribution}</span>
                  </div>
                </div>
              ))}
            </div>
          </AurixCard>
        </div>
      )}

      {/* O2C RISK SUBDOMAIN */}
      {subdomainId === 'o2c' && (
        <div className="space-y-6 animate-pure-fade">
          <AurixCard title="ORDER-TO-CASH & RECEIVABLE RISK MONITOR" badge={<AurixBadge variant="danger">CREDIT EXPOSURE</AurixBadge>}>
            <div className="overflow-x-auto">
              <table className="w-full text-left font-mono text-xs">
                <thead>
                  <tr className="border-b border-white/10 text-slate-400">
                    <th className="pb-3 font-medium">INVOICE ID</th>
                    <th className="pb-3 font-medium">CUSTOMER NAME</th>
                    <th className="pb-3 font-medium text-right">INVOICE AMOUNT (INR)</th>
                    <th className="pb-3 font-medium">DUE DATE</th>
                    <th className="pb-3 font-medium text-right">DSO (DAYS)</th>
                    <th className="pb-3 font-medium text-right">OVERDUE DAYS</th>
                    <th className="pb-3 font-medium text-center">RISK STATUS</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5 text-slate-300">
                  {o2cRisks.map((inv) => (
                    <tr key={inv.invoiceId} className="hover:bg-white/[0.02]">
                      <td className="py-3 text-gold font-bold">{inv.invoiceId}</td>
                      <td className="py-3 text-white">{inv.customerName}</td>
                      <td className="py-3 text-right font-medium">₹{inv.invoiceAmountINR.toLocaleString()}</td>
                      <td className="py-3 text-slate-400">{inv.dueDate}</td>
                      <td className="py-3 text-right">{inv.daysSalesOutstanding}d</td>
                      <td className="py-3 text-right text-[#FF6B6B] font-bold">{inv.overdueDays}d</td>
                      <td className="py-3 text-center">
                        <AurixBadge variant={inv.riskStatus === 'OVERDUE_CRITICAL' ? 'danger' : 'warning'}>
                          {inv.riskStatus}
                        </AurixBadge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </AurixCard>
        </div>
      )}

      {/* OPPORTUNITIES SUBDOMAIN */}
      {subdomainId === 'opportunities' && (
        <div className="space-y-6 animate-pure-fade">
          <AurixCard title="COMMERCIAL EXPANSION & UPSALE PIPELINE" badge={<AurixBadge variant="success">VALUE CAPTURE</AurixBadge>}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 font-mono text-xs">
              {opportunities.map((opp) => (
                <div key={opp.opportunityId} className="p-4 rounded-lg bg-white/[0.02] border border-white/[0.05] space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-white font-bold">{opp.customerName}</span>
                    <AurixBadge variant="success">₹{(opp.estimatedValueINR / 100000).toFixed(1)}L</AurixBadge>
                  </div>
                  <div className="text-slate-400 font-sans text-xs leading-relaxed">{opp.description}</div>
                  <div className="pt-2 border-t border-white/5 text-[11px] text-slate-300">
                    <span className="text-gold font-bold">Action:</span> {opp.suggestedAction}
                  </div>
                </div>
              ))}
            </div>
          </AurixCard>
        </div>
      )}
    </div>
  );
}

export default function SalesPage() {
  return (
    <DomainWorkspaceOrchestrator
      domainKey="sales"
      renderWorkspace={(subdomainId) => <SalesWorkspace subdomainId={subdomainId} />}
    />
  );
}
