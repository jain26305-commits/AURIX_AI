'use client';

import React from 'react';
import { Loader2, AlertTriangle, Database, ShieldAlert, RotateCw } from 'lucide-react';
import { AurixButton } from '@/components/ui/AurixButton';


export const LoadingStateView: React.FC<{ message?: string }> = ({
  message = 'INITIALIZING ENTERPRISE TELEMETRY STREAM...',
}) => {
  return (
    <div className="h-64 flex flex-col items-center justify-center p-8 text-center space-y-4 aurix-card-glass rounded-xl animate-pure-fade">
      <div className="relative">
        <Loader2 className="w-8 h-8 text-[#D4AF37] animate-spin" />
        <div className="absolute inset-0 rounded-full blur-md bg-[#D4AF37]/20" />
      </div>
      <div className="space-y-1">
        <span className="text-xs font-mono font-bold text-white uppercase tracking-[0.2em] block">
          {message}
        </span>
        <span className="text-[10px] font-mono text-slate-500 tracking-wider block">
          RLS ENFORCED • VERIFYING CANONICAL DATA CONTRACTS
        </span>
      </div>
    </div>
  );
};

export const EmptyStateView: React.FC<{
  title?: string;
  description?: string;
  actionText?: string;
  onAction?: () => void;
}> = ({
  title = 'NO ACTIVE DATA RECORDS',
  description = 'No telemetry records or candidate prescriptions match the selected filter criteria.',
  actionText,
  onAction,
}) => {
  return (
    <div className="h-64 flex flex-col items-center justify-center p-8 text-center space-y-4 aurix-card-glass rounded-xl">
      <div className="p-3 rounded-full bg-white/[0.03] border border-white/[0.08] text-slate-500">
        <Database className="w-6 h-6 text-[#D4AF37]" />
      </div>
      <div className="space-y-1 max-w-md">
        <h4 className="text-sm font-bold text-white uppercase font-mono tracking-wide">
          {title}
        </h4>
        <p className="text-xs text-slate-400 font-sans leading-relaxed">
          {description}
        </p>
      </div>
      {actionText && onAction && (
        <AurixButton variant="gold" size="sm" onClick={onAction}>
          {actionText}
        </AurixButton>
      )}
    </div>
  );
};

export const ErrorStateView: React.FC<{
  title?: string;
  message?: string;
  onRetry?: () => void;
}> = ({
  title = 'TELEMETRY STREAM DISRUPTION',
  message = 'An unexpected upstream error occurred while communicating with the domain API gateway.',
  onRetry,
}) => {
  return (
    <div className="h-64 flex flex-col items-center justify-center p-8 text-center space-y-4 aurix-card-glass border-[#FF6B6B]/40 rounded-xl">
      <div className="p-3 rounded-full bg-[#FF6B6B]/10 border border-[#FF6B6B]/30 text-[#FF6B6B]">
        <ShieldAlert className="w-6 h-6" />
      </div>
      <div className="space-y-1 max-w-md">
        <h4 className="text-sm font-bold text-white uppercase font-mono tracking-wide text-[#FF8585]">
          {title}
        </h4>
        <p className="text-xs text-slate-400 font-sans leading-relaxed">
          {message}
        </p>
      </div>
      {onRetry && (
        <AurixButton variant="danger" size="sm" onClick={onRetry} icon={RotateCw}>
          RETRY CONNECTION
        </AurixButton>
      )}
    </div>
  );
};

export const DegradedStateView: React.FC<{
  title?: string;
  message?: string;
}> = ({
  title = 'OPERATING IN DEGRADED TELEMETRY MODE',
  message = 'Live streaming is temporarily buffered. Displaying verified cached baseline snapshot.',
}) => {
  return (
    <div className="p-4 rounded-xl bg-[#F3B33D]/10 border border-[#F3B33D]/30 flex items-center justify-between gap-4 font-mono text-xs">
      <div className="flex items-center gap-3">
        <AlertTriangle className="w-5 h-5 text-[#F3B33D] shrink-0" />
        <div>
          <span className="text-white font-bold block uppercase">{title}</span>
          <span className="text-slate-400 text-[10px] font-sans">{message}</span>
        </div>
      </div>
    </div>
  );
};
