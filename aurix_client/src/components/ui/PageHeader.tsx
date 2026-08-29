'use client';

import React from 'react';
import { ArrowLeft } from 'lucide-react';

export interface PageHeaderProps {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
  onBack?: () => void;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  subtitle,
  action,
  onBack,
}) => {
  return (
    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-white/[0.06] mb-8 relative">
      <div className="absolute top-0 left-0 w-32 h-32 bg-[#D4AF37]/10 blur-[60px] pointer-events-none rounded-full" />
      <div className="flex items-center gap-3 relative z-10">
        {onBack && (
          <button
            onClick={onBack}
            className="p-2.5 rounded-lg bg-white/[0.02] border border-white/[0.05] hover:border-[#D4AF37]/50 hover:bg-[#D4AF37]/10 transition-all text-slate-400 hover:text-[#D4AF37] cursor-pointer"
            title="Return to Domain Landing"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
        )}
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-[0.15em] uppercase drop-shadow-[0_0_15px_rgba(212,175,55,0.1)]">
            {title}
          </h1>
          {subtitle && (
            <p className="text-[10px] font-mono font-bold text-[#D4AF37]/80 mt-1 uppercase tracking-widest">
              {subtitle}
            </p>
          )}
        </div>
      </div>
      {action && <div className="relative z-10">{action}</div>}
    </div>
  );
};
