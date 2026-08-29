'use client';

import React from 'react';

export const ContextSwitcher: React.FC = () => {
  return (
    <div className="px-3 py-1 rounded-lg bg-[#15171A] border border-white/10 text-xs font-mono text-slate-300">
      <span className="text-slate-500 text-[10px]">ENV:</span> PRODUCTION_LIVE
    </div>
  );
};