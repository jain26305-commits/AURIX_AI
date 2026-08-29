'use client';

import React, { useMemo } from 'react';
import { TransitLaneMetrics } from '@/types/logistics.types';
import { Network } from 'lucide-react';

interface NodeDelayHeatmapProps {
  lanes: TransitLaneMetrics[];
}

interface NodeAggregate {
  node: string;
  laneCount: number;
  avgOnTimePercent: number;
  criticalLaneCount: number;
  unitsInTransit: number;
}

export const NodeDelayHeatmap: React.FC<NodeDelayHeatmapProps> = ({ lanes }) => {
  const nodes = useMemo<NodeAggregate[]>(() => {
    const byOrigin = new Map<string, TransitLaneMetrics[]>();
    for (const lane of lanes) {
      const existing = byOrigin.get(lane.origin) || [];
      existing.push(lane);
      byOrigin.set(lane.origin, existing);
    }
    return Array.from(byOrigin.entries())
      .map(([node, nodeLanes]) => ({
        node,
        laneCount: nodeLanes.length,
        avgOnTimePercent: Math.round(
          nodeLanes.reduce((sum, l) => sum + l.onTimeReliabilityPercent, 0) / nodeLanes.length
        ),
        criticalLaneCount: nodeLanes.filter((l) => l.riskLevel === 'CRITICAL').length,
        unitsInTransit: nodeLanes.reduce((sum, l) => sum + l.totalUnitsInTransit, 0),
      }))
      .sort((a, b) => a.avgOnTimePercent - b.avgOnTimePercent);
  }, [lanes]);

  const severityClass = (onTime: number, critical: number) => {
    if (critical > 0 || onTime < 85) return 'bg-[#FF6B6B]/10 border-[#FF6B6B]/30 text-[#FF6B6B]';
    if (onTime < 93) return 'bg-[#F3B33D]/10 border-[#F3B33D]/30 text-[#F3B33D]';
    return 'bg-[#3DDB91]/10 border-[#3DDB91]/30 text-[#3DDB91]';
  };

  if (nodes.length === 0) {
    return (
      <div className="w-full aurix-card-glass rounded-xl p-6 border border-white/[0.08] font-mono text-xs text-slate-500 text-center py-10">
        NO ACTIVE ORIGIN NODES IN CURRENT TRANSIT WINDOW
      </div>
    );
  }

  return (
    <div className="w-full aurix-card-glass rounded-xl p-6 border border-white/[0.08]">
      <div className="flex items-center justify-between pb-4 mb-4 border-b border-white/[0.06]">
        <div>
          <h3 className="text-sm font-semibold text-white tracking-wide flex items-center gap-2">
            <Network className="w-4 h-4 text-[#D4AF37]" />
            ORIGIN NODE DELAY EXPOSURE HEATMAP
          </h3>
          <p className="text-[11px] font-mono text-slate-400 mt-0.5">
            Aggregated on-time reliability and critical lane density by dispatch origin.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 font-mono text-xs">
        {nodes.map((n) => (
          <div
            key={n.node}
            className={`p-4 rounded-xl border transition-all duration-200 ${severityClass(n.avgOnTimePercent, n.criticalLaneCount)}`}
          >
            <div className="text-white font-bold text-xs truncate">{n.node}</div>
            <div className="text-2xl font-bold mt-2">{n.avgOnTimePercent}%</div>
            <div className="text-[9px] text-slate-400 mt-0.5 uppercase tracking-wider">ON-TIME AVG</div>
            <div className="flex items-center justify-between mt-3 pt-2 border-t border-white/[0.06] text-[10px] text-slate-400">
              <span>{n.laneCount} lanes</span>
              <span>{n.unitsInTransit.toLocaleString()} units</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
