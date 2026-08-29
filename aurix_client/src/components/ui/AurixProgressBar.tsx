'use client';

import React from 'react';

export const AurixProgressBar: React.FC<{ progressPercent: number; className?: string }> = ({
  progressPercent,
  className = '',
}) => {
  return (
    <div className={`w-full h-1.5 bg-white/5 rounded-full overflow-hidden ${className}`}>
      <div
        className="h-full bg-gradient-to-r from-[#B8912A] to-[#D4AF37] rounded-full transition-all duration-300"
        style={{ width: `${Math.min(100, Math.max(0, progressPercent))}%` }}
      />
    </div>
  );
};