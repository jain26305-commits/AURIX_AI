'use client';

import React from 'react';
import { Clock, RefreshCw } from 'lucide-react';
import { AurixBadge } from '@/components/ui/AurixBadge';

export interface FreshnessBadgeProps {
  timestamp?: string | Date;
  latencySeconds?: number;
  status?: 'STREAMING' | 'SYNCED' | 'STALE' | 'DEGRADED';
  onRefresh?: () => void;
  className?: string;
}

export const FreshnessBadge: React.FC<FreshnessBadgeProps> = ({
  timestamp = 'Just now',
  latencySeconds = 12,
  status = 'SYNCED',
  onRefresh,
  className = '',
}) => {
  const getStatusVariant = () => {
    switch (status) {
      case 'STREAMING':
      case 'SYNCED':
        return 'success';
      case 'STALE':
        return 'warning';
      case 'DEGRADED':
        return 'danger';
      default:
        return 'gold';
    }
  };

  const displayTime = typeof timestamp === 'string' ? timestamp : timestamp.toLocaleTimeString();

  return (
    <div className={`inline-flex items-center gap-2 font-mono text-[10px] bg-white/[0.02] border border-white/[0.06] px-2.5 py-1 rounded-lg ${className}`}>
      <AurixBadge variant={getStatusVariant()} size="sm" pulse={status === 'STREAMING'}>
        {status}
      </AurixBadge>
      <div className="flex items-center gap-1 text-slate-400">
        <Clock className="w-3 h-3 text-slate-500" />
        <span>SYNC: {displayTime}</span>
        {latencySeconds >= 0 && <span className="text-slate-500">• {latencySeconds}s</span>}
      </div>
      {onRefresh && (
        <button
          onClick={onRefresh}
          className="text-slate-400 hover:text-[#D4AF37] transition-colors p-0.5 ml-1 cursor-pointer"
          title="Trigger Pipeline Re-sync"
        >
          <RefreshCw className="w-3 h-3" />
        </button>
      )}
    </div>
  );
};
