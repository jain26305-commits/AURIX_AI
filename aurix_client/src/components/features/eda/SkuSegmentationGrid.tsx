'use client';

import React from 'react';
import { SkuDemandProfile, AbcClass, XyzClass } from '@/types/eda.types';
import { Grid } from 'lucide-react';
import { AurixBadge } from '@/components/ui/AurixBadge';

interface SkuSegmentationGridProps {
  skuProfiles: SkuDemandProfile[];
  onSelectCell?: (abc: AbcClass, xyz: XyzClass) => void;
}

export const SkuSegmentationGrid: React.FC<SkuSegmentationGridProps> = ({ skuProfiles, onSelectCell }) => {
  const matrix: Record<string, SkuDemandProfile[]> = {
    'A-X': [], 'A-Y': [], 'A-Z': [],
    'B-X': [], 'B-Y': [], 'B-Z': [],
    'C-X': [], 'C-Y': [], 'C-Z': [],
  };

  skuProfiles.forEach((sku) => {
    const key = `${sku.abcClass}-${sku.xyzClass}`;
    if (matrix[key]) {
      matrix[key].push(sku);
    }
  });

  const getCellStyles = (key: string) => {
    if (key === 'A-X') return 'bg-[#3DDB91]/10 border-[#3DDB91]/40 text-[#3DDB91]';
    if (key === 'A-Y' || key === 'B-X') return 'bg-[#B8912A]/15 border-[#D4AF37]/40 text-[#D4AF37]';
    if (key === 'A-Z' || key === 'B-Y' || key === 'C-X') return 'bg-gold/10 border-gold/40 text-gold';
    return 'bg-[#FF6B6B]/10 border-[#FF6B6B]/30 text-[#FF8585]';
  };

  return (
    <div className="w-full aurix-card-glass rounded-xl p-6 border border-white/[0.08]">
      <div className="flex items-center justify-between pb-4 mb-4 border-b border-white/[0.06]">
        <div>
          <h3 className="text-sm font-semibold text-white tracking-wide flex items-center gap-2">
            <Grid className="w-4 h-4 text-gold" />
            ABC / XYZ 9-BOX MATRIX SEGMENTATION
          </h3>
          <p className="text-[11px] font-mono text-slate-400 mt-0.5">
            Cross-classification by Value Contribution (ABC) vs. Demand Volatility (XYZ).
          </p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3 text-xs font-mono">
        {(['A', 'B', 'C'] as AbcClass[]).map((abc) =>
          (['X', 'Y', 'Z'] as XyzClass[]).map((xyz) => {
            const cellKey = `${abc}-${xyz}`;
            const skusInCell = matrix[cellKey] || [];

            return (
              <div
                key={cellKey}
                onClick={() => onSelectCell?.(abc, xyz)}
                className={`p-4 rounded-xl border transition-all duration-200 cursor-pointer flex flex-col justify-between min-h-[6rem] ${getCellStyles(
                  cellKey
                )} hover:scale-[1.02]`}
              >
                <div className="flex items-center justify-between font-bold">
                  <span className="text-sm tracking-wider">{cellKey}</span>
                  <AurixBadge variant="neutral">{skusInCell.length} SKUs</AurixBadge>
                </div>

                <div className="mt-2 space-y-1">
                  {skusInCell.slice(0, 2).map((s) => (
                    <div key={s.skuId} className="text-[10px] truncate text-slate-300">
                      • {s.skuName}
                    </div>
                  ))}
                  {skusInCell.length > 2 && (
                    <div className="text-[9px] text-slate-500 font-medium">
                      +{skusInCell.length - 2} more materials
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};