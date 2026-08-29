"use client";

import React, { useState } from "react";
import { ProvenancePopover } from "@/components/ui/ProvenancePopover";

export interface DecisionOption {
  optionId: string;
  name: string;
  expectedValueUsd: number;
  riskTier: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  implementationLeadTimeDays: number;
}

export interface DecisionCardProps {
  decisionId: string;
  title: string;
  domain: string;
  whyContext: string;
  options: DecisionOption[];
  onApproveOption?: (optionId: string) => void;
  onSimulateScenario?: (optionId: string) => void;
}

export const DecisionCard: React.FC<DecisionCardProps> = ({
  decisionId,
  title,
  domain,
  whyContext,
  options,
  onApproveOption,
  onSimulateScenario,
}) => {
  const [selectedOptionId, setSelectedOptionId] = useState<string>(options[0]?.optionId || "");

  return (
    <div className="p-6 bg-slate-900 border border-slate-800 hover:border-slate-700/80 rounded-2xl transition shadow-xl space-y-4">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-gold/15 text-gold border border-gold/30">
              {domain}
            </span>
            <span className="text-xs font-mono text-slate-500">{decisionId}</span>
          </div>
          <h3 className="text-lg font-bold text-white mt-1">{title}</h3>
        </div>
        <ProvenancePopover
          modelRef="EXPECTED_VALUE_RANKING_2.0"
          sourceDataset="DEMAND_INVENTORY_SENSITIVITY"
          deterministicFormula="EV = Sum(Probability * Delta Margin - Implementation Cost)"
        />
      </div>

      {/* Why Explanation */}
      <div className="p-3 bg-slate-950 border border-slate-800/80 rounded-xl text-xs text-slate-300 leading-relaxed">
        <span className="font-semibold text-slate-200">Context: </span>
        {whyContext}
      </div>

      {/* Options Matrix */}
      <div className="space-y-2">
        <div className="text-xs font-mono text-slate-400 font-semibold uppercase">Action Candidates</div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {options.map((opt) => (
            <div
              key={opt.optionId}
              onClick={() => setSelectedOptionId(opt.optionId)}
              className={`p-3.5 rounded-xl border transition cursor-pointer ${
                selectedOptionId === opt.optionId
                  ? "bg-gold/10 border-gold ring-1 ring-gold"
                  : "bg-slate-950/60 border-slate-800 hover:border-slate-700"
              }`}
            >
              <div className="flex justify-between items-start">
                <span className="text-xs font-bold text-white">{opt.name}</span>
                <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
                  opt.riskTier === "LOW" ? "bg-[#3DDB91]/15 text-[#3DDB91]" : "bg-[#F3B33D]/15 text-[#F3B33D]"
                }`}>
                  {opt.riskTier}
                </span>
              </div>
              <div className="mt-2 flex justify-between items-baseline text-xs font-mono">
                <span className="text-slate-400">Expected Value:</span>
                <span className="text-[#3DDB91] font-bold">+${opt.expectedValueUsd.toLocaleString()}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Action Footer */}
      <div className="pt-2 flex justify-between items-center border-t border-slate-800">
        <button
          onClick={() => onSimulateScenario?.(selectedOptionId)}
          className="text-xs font-medium text-slate-300 hover:text-slate-200 transition"
        >
          🔍 Simulate in What-If Twin ➔
        </button>
        <button
          onClick={() => onApproveOption?.(selectedOptionId)}
          className="px-4 py-2 bg-[#3DDB91] hover:bg-[#3DDB91] text-xs font-bold text-white rounded-lg transition shadow-md"
        >
          Approve & Dispatch Agent
        </button>
      </div>
    </div>
  );
};
