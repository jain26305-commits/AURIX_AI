"use client";

import React from "react";

export type FreshnessStatus = "LIVE" | "RECENT" | "SYNC_DELAYED" | "STALE" | "DEGRADED";

export interface FreshnessBadgeProps {
  status?: FreshnessStatus;
  timestamp?: string;
  source?: string;
}

export const FreshnessBadge: React.FC<FreshnessBadgeProps> = ({
  status = "LIVE",
  timestamp = "Just now",
  source = "Enterprise Fabric",
}) => {
  const badgeStyles: Record<FreshnessStatus, { bg: string; text: string; dot: string }> = {
    LIVE: { bg: "bg-[#3DDB91]/10 border-[#3DDB91]/40", text: "text-[#3DDB91]", dot: "bg-[#3DDB91] animate-pulse" },
    RECENT: { bg: "bg-slate-800/60 border-slate-700/80", text: "text-slate-300", dot: "bg-slate-300" },
    SYNC_DELAYED: { bg: "bg-[#F3B33D]/15 border-[#F3B33D]/40", text: "text-[#F3B33D]", dot: "bg-[#F3B33D]" },
    STALE: { bg: "bg-[#FF6B6B]/10 border-[#FF6B6B]/40", text: "text-[#FF6B6B]", dot: "bg-[#FF6B6B]" },
    DEGRADED: { bg: "bg-gold/10 border-gold/40", text: "text-gold", dot: "bg-gold" },
  };

  const style = badgeStyles[status] || badgeStyles.LIVE;

  return (
    <div className={`inline-flex items-center gap-2 px-2.5 py-1 rounded-full border text-xs font-mono ${style.bg} ${style.text}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${style.dot}`} />
      <span className="font-semibold uppercase">{status}</span>
      <span className="text-slate-500">•</span>
      <span className="text-slate-400">{timestamp}</span>
      <span className="text-slate-600">({source})</span>
    </div>
  );
};
