'use client';

import React from 'react';
import { ModuleReadinessItem } from '@/types/quality.types';
import { Cpu } from 'lucide-react';
import { AurixBadge } from '@/components/ui/AurixBadge';

interface ReadinessMatrixProps {
  items: ModuleReadinessItem[];
}

export const ReadinessMatrix: React.FC<ReadinessMatrixProps> = ({ items }) => {
  return (
    <div className="w-full aurix-card-glass rounded-xl p-6 border border-white/[0.08]">
      <div className="flex items-center justify-between pb-4 mb-4 border-b border-white/[0.06]">
        <div>
          <h3 className="text-sm font-semibold text-white tracking-wide flex items-center gap-2">
            <Cpu className="w-4 h-4 text-[#D4AF37]" />
            ANALYTICAL ENGINE READINESS MATRIX
          </h3>
          <p className="text-[11px] font-mono text-slate-400 mt-0.5">
            Explicit downstream capability clearance preventing execution on corrupt or missing prerequisites.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {items.map((item: any) => {
          const isReady = item.state === 'READY';
          const isPartial = item.state === 'PARTIAL';
          const isBlocked = item.state === 'BLOCKED';

          return (
            <div
              key={item.moduleKey}
              className={`p-5 rounded-xl border flex flex-col justify-between transition-all duration-300 relative overflow-hidden ${
                isReady
                  ? 'bg-[#3DDB91]/5 border-[#3DDB91]/30 text-white'
                  : isPartial
                  ? 'bg-[#F3B33D]/5 border-[#F3B33D]/30 text-white'
                  : 'bg-[#FF6B6B]/5 border-[#FF6B6B]/30 text-white'
              }`}
            >
              {/* Top Accent Line */}
              <div
                className={`absolute inset-x-0 top-0 h-[2px] ${
                  isReady ? 'bg-[#3DDB91]' : isPartial ? 'bg-[#F3B33D]' : 'bg-[#FF6B6B]'
                }`}
              />

              <div>
                <div className="flex items-start justify-between gap-2">
                  <h4 className="text-xs font-mono font-bold tracking-wide uppercase">{item.moduleName}</h4>
                  {isReady && <AurixBadge variant="success">READY</AurixBadge>}
                  {isPartial && <AurixBadge variant="warning">PARTIAL</AurixBadge>}
                  {isBlocked && <AurixBadge variant="danger">BLOCKED</AurixBadge>}
                </div>

                <p className="text-[11px] font-mono text-slate-300 mt-2.5 leading-relaxed">
                  {item.clearanceNote}
                </p>

                {item.unmetPrerequisites.length > 0 && (
                  <div className="mt-3 space-y-1">
                    <span className="text-[10px] font-mono uppercase text-[#FF8585] font-semibold block">
                      Missing Prerequisites:
                    </span>
                    {item.unmetPrerequisites.map((req: any, idx: any) => (
                      <div key={idx} className="text-[10px] font-mono text-slate-400 flex items-center gap-1.5">
                        <span className="w-1 h-1 rounded-full bg-[#FF6B6B]" />
                        <span>{req}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="mt-4 pt-3 border-t border-white/[0.06] flex items-center justify-between text-[10px] font-mono">
                <span className="text-slate-500">GATE CLEARANCE:</span>
                <span className={`font-bold ${isReady ? 'text-[#3DDB91]' : isPartial ? 'text-[#F3B33D]' : 'text-[#FF6B6B]'}`}>
                  {item.score}% PASS RATE
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};