'use client';

import React from 'react';
import { Search } from 'lucide-react';

export interface GlobalSearchProps {
  onOpenPalette: () => void;
}

export const GlobalSearch: React.FC<GlobalSearchProps> = ({ onOpenPalette }) => {
  return (
    <button
      onClick={onOpenPalette}
      className="flex items-center justify-between gap-3 px-3.5 py-1.5 rounded-lg bg-white/[0.02] border border-white/[0.08] hover:border-[#D4AF37]/40 hover:bg-[#D4AF37]/[0.04] text-slate-400 hover:text-white transition-all cursor-pointer group w-48 sm:w-64"
    >
      <div className="flex items-center gap-2 min-w-0">
        <Search className="w-3.5 h-3.5 text-slate-500 group-hover:text-[#D4AF37] transition-colors shrink-0" />
        <span className="font-mono text-xs truncate">Search anything...</span>
      </div>
      <kbd className="hidden sm:inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded font-mono text-[9px] bg-white/[0.04] text-slate-500 border border-white/[0.06] group-hover:text-[#D4AF37]">
        ⌘K
      </kbd>
    </button>
  );
};
