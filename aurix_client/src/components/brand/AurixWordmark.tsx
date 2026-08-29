'use client';

import React from 'react';

export const AurixWordmark: React.FC<{ className?: string }> = ({ className = '' }) => {
  return (
    <div className={`flex flex-col select-none ${className}`}>
      <span className="text-white font-bold tracking-[0.25em] text-lg">AURIX AI</span>
      <span className="text-gold text-[9px] font-mono tracking-[0.3em] uppercase">Enterprise Engine</span>
    </div>
  );
};