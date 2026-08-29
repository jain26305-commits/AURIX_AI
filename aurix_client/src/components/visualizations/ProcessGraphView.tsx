'use client';

import React from 'react';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { CheckCircle2 } from 'lucide-react';

export interface ProcessStep {
  id: string;
  name: string;
  medianDuration: string;
  conformanceRate: string;
  reworkCount: number;
  isBottleneck?: boolean;
}

const DEFAULT_PROCESS_STEPS: ProcessStep[] = [
  { id: 'step-1', name: 'Order Ingestion & Intake', medianDuration: '12 Mins', conformanceRate: '99.8%', reworkCount: 2 },
  { id: 'step-2', name: 'Credit & RLS Governance Check', medianDuration: '45 Mins', conformanceRate: '98.4%', reworkCount: 5 },
  { id: 'step-3', name: 'Inventory Allocation Solver', medianDuration: '1.4 Hrs', conformanceRate: '94.2%', reworkCount: 14, isBottleneck: true },
  { id: 'step-4', name: 'Warehouse Pick & Pack Wave', medianDuration: '3.2 Hrs', conformanceRate: '96.8%', reworkCount: 4 },
  { id: 'step-5', name: 'Carrier Dispatch & Bill of Lading', medianDuration: '45 Mins', conformanceRate: '99.2%', reworkCount: 1 },
];

export const ProcessGraphView: React.FC<{ steps?: ProcessStep[] }> = ({ steps = DEFAULT_PROCESS_STEPS }) => {
  return (
    <AurixCard
      title="OBJECT-CENTRIC PROCESS FLOW (OCPM)"
      subtitle="Autonomous DAG sequence tracking variance, duration, and rework loops"
      badge={<AurixBadge variant="gold">LIVE EVENT STREAM</AurixBadge>}
      className="space-y-6"
    >
      <div className="grid grid-cols-1 md:grid-cols-5 gap-3 relative pt-2">
        {steps.map((step, idx) => {
          return (
            <div
              key={step.id}
              className={`p-4 rounded-xl relative transition-all duration-300 ${
                step.isBottleneck
                  ? 'bg-[#FF6B6B]/10 border-2 border-[#FF6B6B]/60 shadow-[0_0_20px_rgba(255,107,107,0.2)]'
                  : 'bg-white/[0.02] border border-white/[0.05] hover:border-[#D4AF37]/40'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-[9px] font-mono text-slate-500 font-bold">0{idx + 1} • {step.id.toUpperCase()}</span>
                {step.isBottleneck ? (
                  <AurixBadge variant="danger" size="sm">BOTTLENECK</AurixBadge>
                ) : (
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#3DDB91]" />
                )}
              </div>

              <h4 className="text-xs font-bold text-white uppercase font-mono tracking-wide mb-3 min-h-[32px]">
                {step.name}
              </h4>

              <div className="space-y-1 pt-2 border-t border-white/[0.04] font-mono text-[10px]">
                <div className="flex justify-between text-slate-400">
                  <span>MEDIAN DURATION:</span>
                  <span className="text-white font-bold">{step.medianDuration}</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>CONFORMANCE:</span>
                  <span className="text-[#3DDB91] font-bold">{step.conformanceRate}</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>REWORK LOOPS:</span>
                  <span className={step.reworkCount > 5 ? 'text-[#FF6B6B] font-bold' : 'text-slate-300'}>{step.reworkCount} cases</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </AurixCard>
  );
};
