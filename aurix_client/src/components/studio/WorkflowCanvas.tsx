"use client";

import React from "react";
import { WorkflowNodeDTO } from "@/types/agent.types";

export interface WorkflowCanvasProps {
  nodes: WorkflowNodeDTO[];
  onSelectNode?: (nodeId: string) => void;
}

export const WorkflowCanvas: React.FC<WorkflowCanvasProps> = ({ nodes, onSelectNode }) => {
  return (
    <div className="w-full h-80 bg-slate-950 border border-slate-800 rounded-2xl p-6 relative overflow-x-auto flex items-center gap-8 justify-start">
      {nodes.map((n, idx) => (
        <React.Fragment key={n.nodeId}>
          <div
            onClick={() => onSelectNode?.(n.nodeId)}
            className="p-4 bg-slate-900 border border-slate-700 hover:border-gold rounded-xl cursor-pointer transition shadow-lg min-w-48 space-y-2"
          >
            <div className="flex justify-between items-center text-[10px] font-mono">
              <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 uppercase">{n.nodeType}</span>
              <span className="text-slate-500">{n.nodeId}</span>
            </div>
            <div className="font-bold text-xs text-white">{n.name}</div>
            {n.skillRef && <div className="text-[10px] text-slate-300 font-mono">Skill: {n.skillRef}</div>}
            {n.toolRef && <div className="text-[10px] text-gold font-mono">Tool: {n.toolRef}</div>}
          </div>
          {idx < nodes.length - 1 && (
            <div className="text-slate-600 font-mono text-sm flex items-center">
              ──────➔
            </div>
          )}
        </React.Fragment>
      ))}
    </div>
  );
};
