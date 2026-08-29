'use client';

import React from 'react';
import { AurixCard } from '@/components/ui/AurixCard';

export const AurixDistributionPlot: React.FC<{ title?: string }> = ({
  title = 'Probability Distribution',
}) => {
  return (
    <AurixCard title={title}>
      <div className="h-32 flex items-center justify-center text-xs font-mono text-slate-500">
        Normal Gaussian Fit: μ = 118, σ = 14.2
      </div>
    </AurixCard>
  );
};