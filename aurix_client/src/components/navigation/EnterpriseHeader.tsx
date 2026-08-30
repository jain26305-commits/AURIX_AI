'use client';

import React from 'react';
import { GlobalSearch } from '@/components/search/GlobalSearch';
import { ApiClient } from '@/services/api/apiClient';
import {
  Bot,
  BarChart3,
  Bell,
  ChevronRight,
  Layers,
  Sparkles,
} from 'lucide-react';

export interface EnterpriseHeaderProps {
  domainTitle?: string;
  subdomainTitle?: string;
  activeSku?: string;
  activeWorkspaceTitle?: string;
  isExecutiveMode?: boolean;
  onToggleExecutiveMode?: () => void;
  onOpenPalette?: () => void;
  onOpenNotifications?: () => void;
  onOpenAi?: () => void;
}

export const EnterpriseHeader: React.FC<EnterpriseHeaderProps> = ({
  domainTitle,
  subdomainTitle,
  activeSku,
  activeWorkspaceTitle,
  isExecutiveMode = false,
  onToggleExecutiveMode,
  onOpenPalette,
  onOpenNotifications,
  onOpenAi,
}) => {
  const tenantId = ApiClient.getTenantId();

  const displayDomain =
    domainTitle || activeWorkspaceTitle || 'WORKSPACE';

  return (
    <header className="h-[4.25rem] border-b border-white/[0.05] bg-[#030303]/95 backdrop-blur-xl px-6 flex items-center justify-between sticky top-0 z-30 shadow-2xl">
      <div className="flex items-center gap-2.5 font-mono text-[10px] select-none">
        <div className="flex items-center gap-2">
          <Layers className="w-3.5 h-3.5 text-[#D4AF37]" />

          <span className="text-white font-bold tracking-[0.25em] uppercase drop-shadow-[0_0_8px_rgba(212,175,55,0.2)]">
            AURIX
          </span>
        </div>

        <ChevronRight className="w-3 h-3 text-slate-600" />

        <span
          className={`tracking-widest uppercase font-bold transition-colors ${
            subdomainTitle
              ? 'text-slate-500'
              : 'text-[#D4AF37] drop-shadow-[0_0_10px_rgba(212,175,55,0.3)]'
          }`}
        >
          {displayDomain}
        </span>

        {subdomainTitle && (
          <>
            <ChevronRight className="w-3 h-3 text-slate-600" />

            <span className="text-[#D4AF37] font-bold tracking-[0.2em] uppercase bg-[#D4AF37]/10 px-2 py-0.5 rounded border border-[#D4AF37]/30 shadow-[0_0_15px_rgba(212,175,55,0.15)]">
              {subdomainTitle}
            </span>
          </>
        )}

        {activeSku && (
          <>
            <ChevronRight className="w-3 h-3 text-slate-600" />

            <span className="text-white font-bold tracking-widest uppercase bg-white/5 px-2 py-0.5 rounded border border-white/10">
              {activeSku}
            </span>
          </>
        )}
      </div>

      <div className="flex items-center gap-3">
        {onOpenPalette && (
          <GlobalSearch onOpenPalette={onOpenPalette} />
        )}

        {onToggleExecutiveMode && (
          <button
            onClick={onToggleExecutiveMode}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-[10px] uppercase tracking-wider font-mono font-bold transition border border-white/[0.08] bg-white/[0.02] hover:border-[#D4AF37]/40 hover:bg-[#D4AF37]/10 text-white cursor-pointer"
            title="Toggle executive mode"
          >
            {isExecutiveMode ? (
              <Bot className="w-3.5 h-3.5 text-[#D4AF37]" />
            ) : (
              <BarChart3 className="w-3.5 h-3.5 text-slate-400" />
            )}

            {isExecutiveMode ? 'EXECUTIVE' : 'OPERATIONAL'}
          </button>
        )}

        {onOpenAi && (
          <button
            onClick={onOpenAi}
            aria-label="Open AURIX AI"
            title="Open AURIX AI"
            className="group relative flex items-center justify-center gap-3 px-7 py-3.5 min-h-[3.5rem] rounded-xl text-sm md:text-base uppercase tracking-[0.16em] font-mono font-extrabold transition-all duration-300 border border-[#F0D878]/80 bg-gradient-to-r from-[#D4AF37] via-[#F0D878] to-[#D4AF37] text-black cursor-pointer shadow-[0_0_28px_rgba(212,175,55,0.38)] hover:scale-[1.035] focus:outline-none focus:ring-2 focus:ring-[#D4AF37]/70 shrink-0"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>AURIX AI</span>
          </button>
        )}

        {onOpenNotifications && (
          <button
            onClick={onOpenNotifications}
            aria-label="Open notifications"
            className="p-1.5 text-slate-400 hover:text-[#D4AF37] transition rounded-lg hover:bg-[#D4AF37]/10 cursor-pointer"
          >
            <Bell className="w-4 h-4" />
          </button>
        )}

        <div className="flex items-center gap-2 pl-3 border-l border-white/[0.08] text-[10px] font-bold tracking-widest uppercase font-mono text-slate-300">
          <span className="w-2 h-2 rounded-full bg-[#3DDB91] animate-pulse shadow-[0_0_8px_rgba(61,219,145,0.8)]" />
          <span>{tenantId}</span>
        </div>
      </div>
    </header>
  );
};
