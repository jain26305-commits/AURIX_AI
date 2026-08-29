'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { ProcurementStatsBar } from '@/components/features/procurement/ProcurementStatsBar';
import { PurchaseOrderTable } from '@/components/features/procurement/PurchaseOrderTable';
import { ThreeWayMatchCard } from '@/components/features/procurement/ThreeWayMatchCard';
import { AsnTracker } from '@/components/features/procurement/AsnTracker';
import { useProcurement } from '@/hooks/useProcurement';
import { AurixButton } from '@/components/ui/AurixButton';
import { RotateCw, ArrowRight, ShoppingBag, FileCheck2, Truck, Search, Filter } from 'lucide-react';
import { PoLifecycleStatus } from '@/types/procurement.types';
import { useWorkspaceHeader } from '@/context/WorkspaceHeaderContext';

export default function ProcurementPage() {
  useWorkspaceHeader({ activeWorkspaceTitle: "Inbound Procurement" });
  const router = useRouter();
  const {
    data,
    loading,
    activeTab,
    setActiveTab,
    poStatusFilter,
    setPoStatusFilter,
    searchQuery,
    setSearchQuery,
    filteredOrders,
    filteredMatches,
    reload,
  } = useProcurement();

  if (loading || !data) {
    return (
      <>
        <div className="py-24 flex flex-col items-center justify-center text-center space-y-4 font-mono">
          <div className="w-8 h-8 rounded-full border-2 border-gold border-t-transparent animate-spin" />
          <p className="text-xs text-slate-400 tracking-widest uppercase">
            LOADING INBOUND PROCUREMENT & 3-WAY MATCH REGISTRY...
          </p>
        </div>
      </>
    );
  }

  return (
    <>
      <div className="space-y-8 animate-pure-fade font-mono">
        {/* Header Block */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2 py-0.5 rounded bg-gold/10 border border-gold/30 text-gold text-[10px] font-bold tracking-widest uppercase">
                INBOUND SUPPLY CHAIN
              </span>
              <span className="text-slate-500 text-xs">• 3-WAY RECONCILIATION</span>
            </div>
            <h1 className="text-xl font-bold text-white tracking-wide">PROCUREMENT & INBOUND SUPPLY OPERATIONS</h1>
            <p className="text-xs text-slate-400 mt-0.5">
              Purchase order order book, Advance Shipping Notices (ASN), and automated 3-Way Match audits.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <AurixButton variant="secondary" size="sm" onClick={reload}>
              <RotateCw className="w-3.5 h-3.5 mr-1.5" /> RE-SYNC
            </AurixButton>
            <AurixButton variant="gold" size="sm" onClick={() => router.push('/supply-chain?subdomain=planning')}>
              <span>SUPPLIER SCORECARDS</span>
              <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
            </AurixButton>
          </div>
        </div>

        {/* 1. Macro KPI Ribbon */}
        <ProcurementStatsBar summary={data.summary} />

        {/* 2. Sub-Domain Navigation Tabs */}
        <div className="flex items-center gap-2 p-1.5 bg-[#0C0E12] border border-white/[0.08] rounded-xl text-xs select-none">
          <button
            onClick={() => setActiveTab('ORDERS')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold transition-all cursor-pointer ${
              activeTab === 'ORDERS'
                ? 'bg-white/[0.08] text-white border border-white/20'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <ShoppingBag className={`w-3.5 h-3.5 ${activeTab === 'ORDERS' ? 'text-gold' : 'text-slate-500'}`} />
            <span>PURCHASE ORDERS ({data.purchaseOrders.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('THREE_WAY_MATCH')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold transition-all cursor-pointer ${
              activeTab === 'THREE_WAY_MATCH'
                ? 'bg-white/[0.08] text-white border border-white/20'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <FileCheck2 className={`w-3.5 h-3.5 ${activeTab === 'THREE_WAY_MATCH' ? 'text-gold' : 'text-slate-500'}`} />
            <span>3-WAY MATCH AUDIT ({data.matches.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('ASN_TRACKING')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold transition-all cursor-pointer ${
              activeTab === 'ASN_TRACKING'
                ? 'bg-white/[0.08] text-white border border-white/20'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Truck className={`w-3.5 h-3.5 ${activeTab === 'ASN_TRACKING' ? 'text-gold' : 'text-slate-500'}`} />
            <span>ASN TRACKING ({data.asns.length})</span>
          </button>
        </div>

        {/* 3. Search & Filter Bar */}
        {activeTab === 'ORDERS' && (
          <div className="flex flex-wrap items-center justify-between gap-4 p-3 rounded-xl aurix-card-glass border border-white/[0.08] text-xs">
            <div className="flex items-center gap-2">
              <Filter className="w-3.5 h-3.5 text-gold" />
              <span className="text-slate-500 font-bold uppercase">STATUS:</span>
              {(['ALL', 'ISSUED', 'ACKNOWLEDGED', 'IN_TRANSIT', 'RECEIVED'] as const).map((st) => (
                <button
                  key={st}
                  onClick={() => setPoStatusFilter(st as PoLifecycleStatus | 'ALL')}
                  className={`px-2.5 py-1 rounded-lg uppercase transition-colors cursor-pointer ${
                    poStatusFilter === st ? 'bg-white/10 text-white font-bold' : 'text-slate-500 hover:text-slate-300'
                  }`}
                >
                  {st.replace('_', ' ')}
                </button>
              ))}
            </div>

            <div className="relative w-full md:w-64">
              <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by PO# or vendor..."
                className="w-full bg-[#15171A] border border-white/10 rounded-lg pl-8 pr-3 py-1.5 text-white placeholder-slate-500 focus:outline-none focus:border-[#D4AF37]"
              />
            </div>
          </div>
        )}

        {/* 4. Active View Content */}
        {activeTab === 'ORDERS' && <PurchaseOrderTable orders={filteredOrders} />}
        {activeTab === 'THREE_WAY_MATCH' && <ThreeWayMatchCard matches={filteredMatches} />}
        {activeTab === 'ASN_TRACKING' && <AsnTracker asns={data.asns} />}
      </div>
    </>
  );
}