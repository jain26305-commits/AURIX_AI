"use client";

import React from "react";

export interface WaterfallStep {
  label: string;
  amount: number;
  type: "START" | "ADD" | "SUBTRACT" | "TOTAL";
}

export interface WaterfallChartProps {
  title?: string;
  steps: WaterfallStep[];
  currency?: string;
}

export const WaterfallChart: React.FC<WaterfallChartProps> = ({
  title = "P&L Margin Waterfall Decomposition",
  steps,
  currency = "$",
}) => {
  const maxVal = Math.max(...steps.map((s) => Math.abs(s.amount)), 1);

  return (
    <div className="w-full p-5 bg-slate-900 border border-slate-800 rounded-2xl space-y-4">
      <div className="flex justify-between items-center border-b border-slate-800 pb-2">
        <h4 className="text-sm font-bold text-white tracking-wide uppercase font-mono">{title}</h4>
        <span className="text-xs text-slate-500 font-mono">Values in {currency}</span>
      </div>

      <div className="grid grid-cols-5 gap-3 pt-4">
        {steps.map((step, idx) => {
          const heightPct = Math.min(Math.max((Math.abs(step.amount) / maxVal) * 100, 10), 100);
          const isPositive = step.amount >= 0;
          const bg =
            step.type === "TOTAL"
              ? "bg-gold"
              : isPositive
              ? "bg-[#3DDB91]"
              : "bg-[#FF6B6B]";

          return (
            <div key={idx} className="flex flex-col items-center gap-2">
              <div className="text-[11px] font-mono font-bold text-slate-200">
                {isPositive ? "+" : ""}
                {currency}
                {Math.abs(step.amount).toLocaleString()}
              </div>
              <div className="w-full h-36 bg-slate-950 rounded-lg flex items-end justify-center p-1 border border-slate-800">
                <div
                  style={{ height: `${heightPct}%` }}
                  className={`w-full rounded transition-all duration-500 ${bg} opacity-90 hover:opacity-100`}
                />
              </div>
              <div className="text-[11px] font-medium text-slate-400 text-center truncate w-full">
                {step.label}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
