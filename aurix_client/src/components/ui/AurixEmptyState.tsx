'use client';

import React from 'react';
import { PackageOpen } from 'lucide-react';

export const AurixEmptyState: React.FC<{ title: string; description: string }> = ({
  title,
  description,
}) => {
  return (
    <div className="p-12 text-center aurix-card-glass rounded-xl space-y-3 font-mono">
      <PackageOpen className="w-8 h-8 text-slate-500 mx-auto" />
      <h4 className="text-sm font-bold text-white">{title}</h4>
      <p className="text-xs text-slate-400 max-w-sm mx-auto">{description}</p>
    </div>
  );
};