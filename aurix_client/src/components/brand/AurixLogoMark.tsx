'use client';

import React, { forwardRef } from 'react';

export interface AurixLogoMarkProps {
  idPrefix: string;
  iconClassName?: string;
  textClassName?: string;
  trackingClassName?: string;
  className?: string;
  compact?: boolean;
}

export const AurixLogoMark = forwardRef<HTMLDivElement, AurixLogoMarkProps>(
  (
    {
      idPrefix,
      iconClassName = 'w-7 h-7 lg:w-8 lg:h-8',
      textClassName = 'text-xl lg:text-2xl',
      trackingClassName = 'tracking-[0.25em]',
      className = '',
      compact = false,
    },
    ref
  ) => {
    return (
      <div ref={ref} className={`flex items-center select-none ${className}`}>
        <div className={`relative mr-2 flex items-center justify-center shrink-0 ${iconClassName}`}>
          <div className="absolute inset-0 bg-[#B8912A]/25 blur-lg rounded-full" />
          <svg
            viewBox="0 0 100 100"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            className="w-full h-full relative z-10 filter drop-shadow-[0_0_8px_rgba(212,175,55,0.5)]"
          >
            <defs>
              <linearGradient id={`${idPrefix}-leg-left`} x1="15" y1="95" x2="50" y2="5" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stopColor="#94A3B8" />
                <stop offset="50%" stopColor="#F8FAFC" />
                <stop offset="100%" stopColor="#E2E8F0" />
              </linearGradient>
              <linearGradient id={`${idPrefix}-leg-right`} x1="85" y1="95" x2="50" y2="5" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stopColor="#475569" />
                <stop offset="50%" stopColor="#94A3B8" />
                <stop offset="100%" stopColor="#CBD5E1" />
              </linearGradient>
              <linearGradient id={`${idPrefix}-blue-core`} x1="50" y1="95" x2="50" y2="50" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stopColor="#B8912A" />
                <stop offset="100%" stopColor="#D4AF37" />
              </linearGradient>
            </defs>
            <path d="M50 5 L15 95 L30 95 L50 40 Z" fill={`url(#${idPrefix}-leg-left)`} />
            <path d="M50 5 L50 40 L70 95 L85 95 Z" fill={`url(#${idPrefix}-leg-right)`} />
            <path d="M50 58 L36 92 L50 78 L64 92 Z" fill={`url(#${idPrefix}-blue-core)`} />
          </svg>
        </div>

        {!compact && (
          <span
            className={`font-sans ${trackingClassName} text-transparent bg-clip-text bg-gradient-to-b from-[#F8FAFC] via-[#E2E8F0] to-[#94A3B8] font-bold flex items-center ${textClassName}`}
          >
            URIX
            <span className="ml-2 inline-flex items-center gap-[0.08em]">
              <svg
                viewBox="0 0 76 100"
                className="h-[0.80em] w-auto inline-block align-baseline -translate-y-[0.03em]"
                aria-label="A"
              >
                <defs>
                  <linearGradient id={`${idPrefix}-ai-a-grad`} x1="0" y1="0" x2="0" y2="100" gradientUnits="userSpaceOnUse">
                    <stop offset="0%" stopColor="#F8FAFC" />
                    <stop offset="50%" stopColor="#E2E8F0" />
                    <stop offset="100%" stopColor="#94A3B8" />
                  </linearGradient>
                </defs>
                <path d="M38 4 L4 96 L22 96 L38 52 L54 96 L72 96 Z" style={{ fill: `url(#${idPrefix}-ai-a-grad)` }} />
              </svg>
              <span>I</span>
            </span>
          </span>
        )}
      </div>
    );
  }
);

AurixLogoMark.displayName = 'AurixLogoMark';