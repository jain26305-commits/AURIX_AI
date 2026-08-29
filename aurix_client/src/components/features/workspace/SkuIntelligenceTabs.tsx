'use client';

import React from 'react';
import { SkuUnifiedStory } from '@/types/sku-workspace.types';
import { AurixForecastBands } from '@/components/charts/AurixForecastBands';
import { AurixTimeSeriesChart } from '@/components/charts/AurixTimeSeriesChart';
import { SafetyStockCalculator } from '@/components/features/inventory/SafetyStockCalculator';
import { SupplierScorecard } from '@/components/features/supply/SupplierScorecard';
import { LeadTimeDistributionCard } from '@/components/features/supply/LeadTimeDistributionCard';
import { RecommendationCard } from '@/components/features/recommendations/RecommendationCard';
import { AurixCard } from '@/components/ui/AurixCard';

import { TrendingUp, Package, Truck, Sparkles } from 'lucide-react';

interface SkuIntelligenceTabsProps {
  story: SkuUnifiedStory;
  activeTab: 'FORECAST' | 'INVENTORY' | 'SUPPLY' | 'RECOMMENDATIONS';
  onTabChange: (tab: 'FORECAST' | 'INVENTORY' | 'SUPPLY' | 'RECOMMENDATIONS') => void;
}

export const SkuIntelligenceTabs: React.FC<SkuIntelligenceTabsProps> = ({
  story,
  activeTab,
  onTabChange,
}) => {
  const tabs = [
    { key: 'FORECAST', label: 'ML FORECAST & DEMAND', icon: TrendingUp },
    { key: 'INVENTORY', label: 'INVENTORY & BUFFERS', icon: Package },
    { key: 'SUPPLY', label: 'SUPPLIER & LEAD TIME', icon: Truck },
    { key: 'RECOMMENDATIONS', label: `AI ADVISOR (${story.activeRecommendations.length})`, icon: Sparkles },
  ] as const;

  return (
    <div className="space-y-6">
      {/* Navigation Tab Conduit */}
      <div className="flex items-center gap-2 p-1.5 bg-[#0C0E12] border border-white/[0.08] rounded-xl text-xs font-mono select-none overflow-x-auto">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => onTabChange(tab.key)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold transition-all cursor-pointer whitespace-nowrap ${
                isActive
                  ? 'bg-white/[0.08] text-white border border-white/20 shadow-[inset_0_1px_1px_rgba(255,255,255,0.1)]'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.02]'
              }`}
            >
              <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-gold' : 'text-slate-500'}`} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab Panels */}
      {activeTab === 'FORECAST' && (
        <div className="space-y-6 animate-pure-fade">
          <AurixForecastBands timeline={story.forecast.timeline} height={300} />
          <AurixCard title="12-MONTH HISTORICAL DEMAND TRAJECTORY">
            <AurixTimeSeriesChart data={story.demand.monthlyHistory} accentColor="blue" height={200} />
          </AurixCard>
        </div>
      )}

      {activeTab === 'INVENTORY' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 animate-pure-fade">
          <div className="lg:col-span-6">
            <SafetyStockCalculator
              activeSku={story.inventory}
              serviceLevel={story.inventory.serviceLevelTargetPercent}
              onServiceLevelChange={() => {}}
              adjustedSafetyStock={story.inventory.safetyStockUnits}
              adjustedRop={story.inventory.reorderPointUnits}
            />
          </div>
          <div className="lg:col-span-6 space-y-4 text-xs font-mono">
            <AurixCard title="BALANCE SHEET ALLOCATION">
              <div className="space-y-3">
                <div className="flex justify-between py-2 border-b border-white/[0.04]">
                  <span className="text-slate-400">Unit Cost:</span>
                  <span className="text-white font-bold">₹420</span>
                </div>
                <div className="flex justify-between py-2 border-b border-white/[0.04]">
                  <span className="text-slate-400">Total Capital Locked:</span>
                  <span className="text-gold font-bold">₹{story.inventory.capitalTiedUpINR.toLocaleString()}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-white/[0.04]">
                  <span className="text-slate-400">Stockout Revenue Exposure:</span>
                  <span className="text-[#FF8585] font-bold">₹{story.inventory.stockoutRevenueAtRiskINR.toLocaleString()}</span>
                </div>
                <div className="flex justify-between py-2">
                  <span className="text-slate-400">Stockout Breach Probability:</span>
                  <span className="text-white font-bold">{story.inventory.stockoutProbabilityPercent}%</span>
                </div>
              </div>
            </AurixCard>
          </div>
        </div>
      )}

      {activeTab === 'SUPPLY' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 animate-pure-fade">
          <div className="lg:col-span-5">
            <SupplierScorecard supplier={story.supplier} />
          </div>
          <div className="lg:col-span-7">
            <LeadTimeDistributionCard leadTime={story.supplier.leadTime} supplierName={story.supplier.supplierName} />
          </div>
        </div>
      )}

      {activeTab === 'RECOMMENDATIONS' && (
        <div className="space-y-4 animate-pure-fade">
          {story.activeRecommendations.length > 0 ? (
            story.activeRecommendations.map((rec) => (
              <RecommendationCard
                key={rec.id}
                item={rec}
                onOpenApproval={() => {}}
                onOpenProvenance={() => {}}
                onReject={() => {}}
                onSimulate={() => {}}
              />
            ))
          ) : (
            <div className="p-12 text-center aurix-card-glass rounded-xl text-xs font-mono text-slate-400">
              No active critical signals logged for this variant. Operational posture is optimal.
            </div>
          )}
        </div>
      )}
    </div>
  );
};