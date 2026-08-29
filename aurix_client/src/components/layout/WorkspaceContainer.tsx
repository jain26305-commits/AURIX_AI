'use client';

import React from 'react';

export const WorkspaceContainer: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = '',
}) => {
  return <div className={`space-y-8 animate-pure-fade ${className}`}>{children}</div>;
};