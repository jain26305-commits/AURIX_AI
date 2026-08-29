"use client";

import React from "react";
import { ScenarioComparisonReport } from "@/types/scenario.types";
import { Award, CheckCircle, TrendingUp } from "lucide-react";

interface ScenarioComparisonProps {
  report: ScenarioComparisonReport;
}

export const ScenarioComparison: React.FC<ScenarioComparisonProps> = ({ report }) => {
  const { comparison_matrix, baseline_scenario_id, recommended_scenario_id, tradeoffs_explanation } = report;

  const baseline = comparison_matrix.find((s) => s.is_baseline || s.scenario_id === baseline_scenario_id);
  const candidates = comparison_matrix.filter((s) => !s.is_baseline && s.scenario_id !== baseline_scenario_id);

  return (
    <div className="w-full p-5 bg-[#0C0E12] border border-white/[0.08] rounded-2xl overflow-hidden space-y-4 font-mono select-none">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-white/[0.06] pb-3">
        <div>
          <h4 className="text-sm font-bold text-white tracking-wide uppercase flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-gold" />
            DETERMINISTIC SCENARIO DELTA COMPARISON
          </h4>
          <span className="text-[11px] text-slate-400 font-sans">
            Side-by-side trade-off matrix evaluated against Do-Nothing baseline.
          </span>
        </div>
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-gold/10 border border-gold/30 text-gold text-[10px] font-bold">
          <Award className="w-3.5 h-3.5" />
          OPTIMAL: {recommended_scenario_id}
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-white/[0.06] text-slate-400 text-[10px] uppercase tracking-wider">
              <th className="p-2.5">Evaluated Parameter</th>
              <th className="p-2.5 text-slate-500">
                BASELINE ({baseline?.scenario_id || "CONTROL"})
              </th>
              {candidates.map((cand) => (
                <th
                  key={cand.scenario_id}
                  className={`p-2.5 ${
                    cand.scenario_id === recommended_scenario_id ? "text-gold font-bold" : "text-slate-300"
                  }`}
                >
                  {cand.scenario_id} {cand.scenario_id === recommended_scenario_id && "★"}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.04] text-[11px]">
            <tr className="hover:bg-white/[0.02]">
              <td className="p-2.5 text-slate-300 font-sans font-medium">Simulated Revenue</td>
              <td className="p-2.5 text-slate-500">${(baseline?.revenue_usd || 0).toLocaleString()}</td>
              {candidates.map((c) => (
                <td key={c.scenario_id} className="p-2.5 text-white font-bold">
                  ${c.revenue_usd.toLocaleString()}
                </td>
              ))}
            </tr>
            <tr className="hover:bg-white/[0.02]">
              <td className="p-2.5 text-slate-300 font-sans font-medium">Operating Margin</td>
              <td className="p-2.5 text-slate-500">${(baseline?.margin_usd || 0).toLocaleString()}</td>
              {candidates.map((c) => (
                <td key={c.scenario_id} className="p-2.5 text-white font-bold">
                  ${c.margin_usd.toLocaleString()}
                </td>
              ))}
            </tr>
            <tr className="hover:bg-white/[0.02]">
              <td className="p-2.5 text-slate-300 font-sans font-medium">Working Capital Requirement</td>
              <td className="p-2.5 text-slate-500">${(baseline?.working_capital_usd || 0).toLocaleString()}</td>
              {candidates.map((c) => (
                <td key={c.scenario_id} className="p-2.5 text-slate-300">
                  ${c.working_capital_usd.toLocaleString()}
                </td>
              ))}
            </tr>
            <tr className="hover:bg-white/[0.02]">
              <td className="p-2.5 text-slate-300 font-sans font-medium">Residual Risk Exposure</td>
              <td className="p-2.5 text-slate-500">${(baseline?.risk_exposure_usd || 0).toLocaleString()}</td>
              {candidates.map((c) => (
                <td key={c.scenario_id} className="p-2.5 text-[#FF6B6B]">
                  ${c.risk_exposure_usd.toLocaleString()}
                </td>
              ))}
            </tr>
            <tr className="bg-gold/5 font-bold border-t border-gold/20">
              <td className="p-2.5 text-gold font-sans">Net Expected Value (EV)</td>
              <td className="p-2.5 text-slate-500">${(baseline?.expected_value_usd || 0).toLocaleString()}</td>
              {candidates.map((c) => (
                <td key={c.scenario_id} className="p-2.5 text-gold">
                  ${c.expected_value_usd.toLocaleString()}
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>

      {tradeoffs_explanation && (
        <div className="p-3 rounded-xl bg-white/[0.02] border border-white/[0.04] text-[11px] font-sans text-slate-300 flex items-start gap-2">
          <CheckCircle className="w-4 h-4 text-[#3DDB91] shrink-0 mt-0.5" />
          <span>{tradeoffs_explanation}</span>
        </div>
      )}
    </div>
  );
};
