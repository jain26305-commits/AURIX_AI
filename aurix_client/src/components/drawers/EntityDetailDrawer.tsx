"use client";

import React from "react";
import { FreshnessBadge } from "../ui/FreshnessBadge";

export interface EntityDetailDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  entityType: string;
  entityId: string;
  title: string;
  attributes: Record<string, any>;
  linkedDecisions?: Array<{ id: string; name: string }>;
}

export const EntityDetailDrawer: React.FC<EntityDetailDrawerProps> = ({
  isOpen,
  onClose,
  entityType,
  entityId,
  title,
  attributes,
  linkedDecisions = [],
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm transition">
      <div className="w-full max-w-md h-full bg-slate-900 border-l border-slate-800 p-6 flex flex-col justify-between shadow-2xl overflow-y-auto">
        <div className="space-y-6">
          {/* Header */}
          <div className="flex justify-between items-start border-b border-slate-800 pb-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                  {entityType}
                </span>
                <span className="text-xs font-mono text-slate-500">{entityId}</span>
              </div>
              <h2 className="text-xl font-bold text-white mt-1">{title}</h2>
            </div>
            <button onClick={onClose} className="text-slate-400 hover:text-white p-1">✕</button>
          </div>

          <FreshnessBadge status="LIVE" timestamp="Synced 2m ago" source="PostgreSQL RLS" />

          {/* Attributes List */}
          <div className="space-y-3">
            <h4 className="text-xs font-mono font-semibold uppercase text-slate-400">Attributes</h4>
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-2 text-xs">
              {Object.entries(attributes).map(([key, val]) => (
                <div key={key} className="flex justify-between items-center">
                  <span className="text-slate-400 capitalize">{key.replace(/_/g, " ")}:</span>
                  <span className="font-mono text-slate-200 font-semibold">{String(val)}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Linked Decisions */}
          {linkedDecisions.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-mono font-semibold uppercase text-slate-400">Active Decisions</h4>
              {linkedDecisions.map((dec) => (
                <div key={dec.id} className="p-3 bg-slate-950 border border-gold/20 rounded-xl text-xs flex justify-between items-center">
                  <span className="text-slate-200">{dec.name}</span>
                  <span className="text-gold font-mono text-[11px]">{dec.id}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="pt-4 border-t border-slate-800 flex gap-3">
          <button onClick={onClose} className="w-full py-2 bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-white rounded-lg transition">
            Close Panel
          </button>
        </div>
      </div>
    </div>
  );
};
