'use client';

import React, { useState } from 'react';

export const AurixTooltip: React.FC<{ text: string; children: React.ReactNode }> = ({
  text,
  children,
}) => {
  const [visible, setVisible] = useState(false);

  return (
    <div
      className="relative inline-block"
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
    >
      {children}
      {visible && (
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2.5 py-1 bg-[#15171A] border border-white/20 rounded-md text-[10px] font-mono text-white whitespace-nowrap shadow-2xl z-50 pointer-events-none">
          {text}
        </div>
      )}
    </div>
  );
};