'use client';

import React from 'react';

export default function Loading() {
  return (
    <div className="min-h-[60vh] w-full flex flex-col items-center justify-center space-y-4">
      {/* Glowing Dual Ring Loader */}
      <div className="relative flex items-center justify-center">
        <div className="w-10 h-10 rounded-full border-2 border-white/10 border-t-[#D4AF37] animate-spin" />
        <div className="absolute inset-0 rounded-full bg-[#B8912A]/20 blur-md" />
      </div>

      {/* Telemetry Text */}
      <div className="text-center space-y-1">
        <p className="text-xs font-mono font-semibold tracking-[0.25em] text-white uppercase">
          INITIALIZING WORKSPACE
        </p>
        <p className="text-[10px] font-mono text-slate-500 tracking-widest uppercase">
          SYNCHRONIZING DETERMINISTIC PIPELINE...
        </p>
      </div>
    </div>
  );
}