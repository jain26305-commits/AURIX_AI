'use client';

import React from 'react';
import { RecommendationItem } from '@/types/recommendation.types';
import { X, Database, FileCode } from 'lucide-react';


interface ProvenanceTraceDrawerProps {
  item: RecommendationItem | null;
  isOpen: boolean;
  onClose: () => void;
}

export const ProvenanceTraceDrawer: React.FC<ProvenanceTraceDrawerProps> = ({
  item,
  isOpen,
  onClose,
}) => {
  if (!isOpen || !item) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm animate-pure-fade select-none">
      <div className="w-full max-w-xl bg-[#0C0E12] border-l border-white/10 h-full p-6 overflow-y-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-white/10">
          <div>
            <h3 className="text-base font-bold text-white tracking-wide flex items-center gap-2">
              <Database className="w-5 h-5 text-gold" />
              DECISION PROVENANCE TRACE
            </h3>
            <span className="text-xs font-mono text-slate-400">Audit Provenance for {item.id}</span>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-white/[0.05] hover:bg-white/10 text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Section 1: Engine Pipeline Metadata */}
        <div className="space-y-2 text-xs font-mono">
          <span className="text-[10px] text-gold uppercase tracking-widest font-bold block">1. INFERENCE METADATA</span>
          <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06] space-y-2.5 text-slate-300">
            <div className="flex items-center justify-between">
              <span className="text-slate-500">Source Feed:</span>
              <span className="text-white font-medium">{item.provenance.dataSource}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-500">Analytical Engine:</span>
              <span className="text-gold font-bold">{item.provenance.modelUsed}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-500">Data Quality Score:</span>
              <span className="text-[#3DDB91] font-bold">{item.provenance.dataQualityPassRate}%</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-500">Evaluated At:</span>
              <span className="text-slate-300">{item.provenance.evaluatedTimestamp}</span>
            </div>
          </div>
        </div>

        {/* Section 2: Mathematical Assumptions */}
        <div className="space-y-2 text-xs font-mono">
          <span className="text-[10px] text-gold uppercase tracking-widest font-bold block">2. MODEL ASSUMPTIONS</span>
          <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06] space-y-2">
            {item.provenance.assumptions.map((assump, idx) => (
              <div key={idx} className="flex items-start gap-2 text-slate-300 text-[11px] leading-relaxed">
                <span className="text-gold font-bold">•</span>
                <span>{assump}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Section 3: Cryptographic Integrity Checksum */}
        <div className="space-y-2 text-xs font-mono">
          <span className="text-[10px] text-gold uppercase tracking-widest font-bold block">3. VERIFIED DATASET CHECKSUM</span>
          <div className="p-3.5 rounded-xl bg-black/40 border border-white/[0.08] text-[10px] text-slate-400 break-all">
            <FileCode className="w-3.5 h-3.5 text-[#D4AF37] inline-block mr-1.5" />
            {item.provenance.datasetChecksum}
          </div>
        </div>
      </div>
    </div>
  );
};