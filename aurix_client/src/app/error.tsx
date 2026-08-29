'use client';

import React, { useEffect } from 'react';
import { AurixButton } from '@/components/ui/AurixButton';
import { AlertOctagon, RotateCw, Home } from 'lucide-react';
import Link from 'next/link';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('[AURIX Platform Error Boundary Catch]:', error);
  }, [error]);

  return (
    <div className="min-h-[70vh] w-full flex flex-col items-center justify-center p-6 text-center space-y-6 select-none animate-pure-fade">
      <div className="relative flex items-center justify-center">
        <div className="w-16 h-16 rounded-2xl bg-[#FF6B6B]/10 border border-[#FF6B6B]/30 flex items-center justify-center text-[#FF6B6B] shadow-[0_0_30px_rgba(255,107,107,0.2)]">
          <AlertOctagon className="w-8 h-8" />
        </div>
        <div className="absolute inset-0 rounded-full bg-[#FF6B6B]/10 blur-xl pointer-events-none" />
      </div>

      <div className="space-y-2 max-w-md">
        <h2 className="text-lg font-bold text-white tracking-wide">
          ANALYTICAL WORKSPACE ENCOUNTERED AN ERROR
        </h2>
        <p className="text-xs font-mono text-slate-400 leading-relaxed">
          {error.message || 'An unexpected operational pipeline exception occurred.'}
        </p>
        {error.digest && (
          <span className="text-[10px] font-mono text-slate-600 block">Digest: {error.digest}</span>
        )}
      </div>

      <div className="flex items-center gap-3 pt-2">
        <AurixButton variant="secondary" size="md" onClick={() => reset()}>
          <RotateCw className="w-3.5 h-3.5 mr-1.5" />
          <span>RETRY PIPELINE</span>
        </AurixButton>
        <Link href="/control-tower">
          <AurixButton variant="gold" size="md">
            <Home className="w-3.5 h-3.5 mr-1.5" />
            <span>RETURN TO CONTROL TOWER</span>
          </AurixButton>
        </Link>
      </div>
    </div>
  );
}