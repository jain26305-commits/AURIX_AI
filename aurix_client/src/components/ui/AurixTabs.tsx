'use client';

import React from 'react';

interface TabItem {
  key: string;
  label: string;
}

interface AurixTabsProps {
  tabs: TabItem[];
  activeKey: string;
  onChange: (key: string) => void;
}

export const AurixTabs: React.FC<AurixTabsProps> = ({ tabs, activeKey, onChange }) => {
  return (
    <div className="flex items-center gap-2 p-1 bg-[#15171A] border border-white/10 rounded-xl text-xs font-mono">
      {tabs.map((tab) => (
        <button
          key={tab.key}
          onClick={() => onChange(tab.key)}
          className={`px-3 py-1.5 rounded-lg transition-all font-bold cursor-pointer ${
            activeKey === tab.key
              ? 'bg-white/10 text-white border border-white/20'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
};