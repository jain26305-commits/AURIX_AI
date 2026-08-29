"use client";

import React from "react";

export interface TabItem {
  id: string;
  label: string;
  badge?: number | string;
}

export interface SubNavProps {
  tabs: TabItem[];
  activeTab: string;
  onChange: (id: string) => void;
}

export const SubNav: React.FC<SubNavProps> = ({ tabs, activeTab, onChange }) => {
  return (
    <div className="flex gap-2 border-b border-slate-800 mb-6 overflow-x-auto">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className={`pb-3 px-3 text-xs font-mono font-semibold transition border-b-2 flex items-center gap-2 ${
            activeTab === tab.id
              ? "border-slate-300 text-slate-300"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <span>{tab.label}</span>
          {tab.badge !== undefined && (
            <span className="px-1.5 py-0.2 rounded-full bg-slate-800 text-[10px] text-slate-300">
              {tab.badge}
            </span>
          )}
        </button>
      ))}
    </div>
  );
};
