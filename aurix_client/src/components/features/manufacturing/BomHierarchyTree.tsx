'use client';

import React from 'react';
import { BomHierarchy } from '@/types/manufacturing.types';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { Layers, GitCommit } from 'lucide-react';
import { formatINR } from '@/lib/formatters';

interface BomHierarchyTreeProps {
  bom: BomHierarchy;
  availableBoms?: any[];
  selectedSkuId: string;
  onSelectSku: (skuId: string) => void;
}

export const BomHierarchyTree: React.FC<BomHierarchyTreeProps> = ({
  bom,
  availableBoms,
  selectedSkuId,
  onSelectSku,
}) => {
  return (
    <div className="w-full aurix-card-glass rounded-xl p-6 border border-white/[0.08] select-none font-mono space-y-6">
      {/* Header & Material Switcher */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-white/[0.06]">
        <div>
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-gold" />
            <h3 className="text-sm font-bold text-white tracking-wide">
              MULTI-LEVEL BILL OF MATERIALS (BOM) / {bom.parentSkuId}
            </h3>
            <AurixBadge variant="gold">{bom.version}</AurixBadge>
          </div>
          <span className="text-slate-400 text-[11px] mt-0.5 block">
            {bom.parentSkuName} • Target Yield: {bom.yieldRatePercent}%
          </span>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-[10px] text-slate-500 uppercase">PARENT PRODUCT:</span>
          <select
            value={selectedSkuId}
            onChange={(e) => onSelectSku(e.target.value)}
            className="bg-[#15171A] border border-white/15 rounded-lg px-3 py-1.5 text-slate-200 font-mono text-xs focus:outline-none focus:border-[#D4AF37]"
          >
            {(availableBoms || []).map((b: any) => (
              <option key={b.parentSkuId} value={b.parentSkuId}>
                {b.parentSkuId} — {b.parentSkuName}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* BOM Tree Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-white/[0.08] text-slate-500 text-[10px] uppercase tracking-wider">
              <th className="pb-3 pl-2">Level & Component Item</th>
              <th className="pb-3">Category</th>
              <th className="pb-3">Qty / Parent</th>
              <th className="pb-3">Scrap Factor</th>
              <th className="pb-3">Lead Time</th>
              <th className="pb-3">Unit Cost</th>
              <th className="pb-3">Extended Cost</th>
              <th className="pb-3 text-right pr-2">Approved Supplier</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.04]">
            {(bom.components || []).map((c: any) => {
              const isSubAssembly = c.level === 1;

              return (
                <tr key={c.componentId} className="hover:bg-white/[0.02] transition-colors">
                  <td className="py-3 pl-2">
                    <div className="flex items-center gap-2" style={{ paddingLeft: `${(c.level - 1) * 20}px` }}>
                      <GitCommit className={`w-3.5 h-3.5 ${isSubAssembly ? 'text-gold' : 'text-[#D4AF37]'}`} />
                      <div className="flex flex-col">
                        <span className={`font-bold ${isSubAssembly ? 'text-white' : 'text-slate-300'}`}>
                          {c.componentName}
                        </span>
                        <span className="text-[10px] text-slate-500">
                          Level 0{c.level} • {c.componentId}
                        </span>
                      </div>
                    </div>
                  </td>

                  <td className="py-3">
                    <AurixBadge variant={c.category === 'FABRIC' ? 'gold' : c.category === 'TRIM' ? 'info' : 'neutral'}>
                      {c.category}
                    </AurixBadge>
                  </td>

                  <td className="py-3 text-white font-bold">
                    {c.quantityPerParent} {c.unitOfMeasure}
                  </td>

                  <td className="py-3">
                    <span className={c.scrapFactorPercent > 3.0 ? 'text-[#F3B33D]' : 'text-slate-400'}>
                      +{c.scrapFactorPercent}%
                    </span>
                  </td>

                  <td className="py-3 text-slate-400">{c.leadTimeDays}d</td>

                  <td className="py-3 text-slate-300">{formatINR(c.unitCostINR)}</td>

                  <td className="py-3 text-gold font-bold">{formatINR(c.extendedCostINR)}</td>

                  <td className="py-3 text-right pr-2 text-slate-400 text-[11px]">
                    {c.supplierName}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* BOM Cost Rollup Footer */}
      <div className="pt-3 border-t border-white/[0.06] flex items-center justify-between text-xs">
        <span className="text-slate-400">TOTAL ROLLED-UP UNIT BOM COST:</span>
        <span className="text-base font-bold text-gold">{formatINR(bom.totalBomCostINR)} / unit</span>
      </div>
    </div>
  );
};