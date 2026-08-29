'use client';

import React from 'react';
import { Account360DTO } from '@/types/commercial.types';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { formatINR } from '@/lib/formatters';
import { Users } from 'lucide-react';

interface AccountHealthGridProps {
  accounts: Account360DTO[];
  selectedAccountId: string | null;
  onSelectAccount: (id: string) => void;
}

const healthBadgeVariant: Record<Account360DTO['healthStatus'], 'success' | 'gold' | 'warning' | 'danger'> = {
  THRIVING: 'success',
  STABLE: 'gold',
  AT_RISK: 'warning',
  DORMANT: 'danger',
  CHURNED: 'danger',
};

export const AccountHealthGrid: React.FC<AccountHealthGridProps> = ({ accounts, selectedAccountId, onSelectAccount }) => {
  return (
    <AurixCard title="ACCOUNT 360 & CUSTOMER HEALTH" badge={<AurixBadge variant="gold">{accounts.length} ACCOUNTS</AurixBadge>}>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 font-mono text-xs">
        {accounts.map((acc) => {
          const isSelected = acc.customerId === selectedAccountId;
          return (
            <div
              key={acc.customerId}
              onClick={() => onSelectAccount(acc.customerId)}
              className={`p-4 rounded-xl border cursor-pointer transition-all ${
                isSelected
                  ? 'bg-gold/5 border-gold/40'
                  : 'bg-white/[0.02] border-white/[0.06] hover:border-white/20'
              }`}
            >
              <div className="flex items-start justify-between gap-2 mb-2">
                <div className="min-w-0 flex items-center gap-2">
                  <Users className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                  <span className="text-white font-bold truncate">{acc.customerName}</span>
                </div>
                <AurixBadge variant={healthBadgeVariant[acc.healthStatus]} size="sm">{acc.healthStatus}</AurixBadge>
              </div>
              <div className="grid grid-cols-3 gap-2 text-[10px] pt-2 border-t border-white/[0.05]">
                <div>
                  <span className="text-slate-500 block">HEALTH</span>
                  <span className="text-white font-bold">{acc.healthScore}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">PERIOD REV</span>
                  <span className="text-white font-bold">{formatINR(acc.periodRevenue, false)}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">OTIF</span>
                  <span className={acc.otifRatePct >= 95 ? 'text-[#3DDB91] font-bold' : 'text-[#F3B33D] font-bold'}>
                    {acc.otifRatePct}%
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </AurixCard>
  );
};
