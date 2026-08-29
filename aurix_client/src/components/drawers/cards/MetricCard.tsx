"use client";

import React from "react";
import { AnimatedCounter } from "@/components/charts/AnimatedCounter";

export interface MetricCardProps {
  title: string;
  value: number;
  deltaPct?: number;
  deltaLabel?: string;
  prefix?: string;
  suffix?: string;
  decimals?: number;
  statusColor?: "neutral" | "success" | "warning" | "danger" | "gold";
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  deltaPct,
  deltaLabel = "vs last period",
  prefix = "",
  suffix = "",
  decimals = 0,
  statusColor = "neutral",
}) => {
  const colorMap = {
    neutral: "text-slate-300 border-white/10 bg-white/[0.02]",
    success: "text-[#3DDB91] border-[#3DDB91]/20 bg-[#3DDB91]/10",
    warning: "text-[#F3B33D] border-[#F3B33D]/20 bg-[#F3B33D]/10",
    danger: "text-[#FF6B6B] border-[#FF6B6B]/20 bg-[#FF6B6B]/10",
    gold: "text-gold border-gold/20 bg-gold/10",
  };

  const isPositiveDelta = deltaPct !== undefined && deltaPct >= 0;

  return (
    <div className="p-5 bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-2xl transition duration-200 shadow-lg">
      <div className="text-xs font-mono font-semibold uppercase text-slate-400 tracking-wider">
        {title}
      </div>
      <div className={`text-2xl sm:text-3xl font-bold font-mono mt-2 tracking-tight ${colorMap[statusColor].split(" ")[0]}`}>
        <AnimatedCounter value={value} prefix={prefix} suffix={suffix} decimals={decimals} />
      </div>
      {deltaPct !== undefined && (
        <div className="flex items-center gap-1.5 mt-2 text-xs font-mono">
          <span className={isPositiveDelta ? "text-[#3DDB91]" : "text-[#FF6B6B]"}>
            {isPositiveDelta ? "▲ +" : "▼ "}
            {deltaPct.toFixed(1)}%
          </span>
          <span className="text-slate-500">{deltaLabel}</span>
        </div>
      )}
    </div>
  );
};
