'use client';

import React from 'react';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en">
      <body className="bg-[#030303] text-[#F8FAFC] min-h-screen flex flex-col items-center justify-center p-6 font-mono text-center">
        <div className="max-w-md space-y-4">
          <h1 className="text-xl font-bold text-[#FF6B6B]">CRITICAL SYSTEM FAULT</h1>
          <p className="text-xs text-[#94A3B8]">{error.message || 'Global application crash occurred.'}</p>
          <button
            onClick={() => reset()}
            className="px-4 py-2 bg-[#D4AF37]/20 border border-[#D4AF37]/40 text-[#F0D878] rounded-lg text-xs font-bold cursor-pointer"
          >
            RELOAD SYSTEM
          </button>
        </div>
      </body>
    </html>
  );
}