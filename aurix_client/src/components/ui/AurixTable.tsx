'use client';

import React from 'react';

export const AurixTable: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = '',
}) => {
  return (
    <div className={`overflow-x-auto w-full ${className}`}>
      <table className="w-full text-left text-xs font-mono">{children}</table>
    </div>
  );
};