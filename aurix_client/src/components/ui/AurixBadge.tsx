'use client';

import React from 'react';

export interface AurixBadgeProps {
  children: React.ReactNode;
  variant?: 'gold' | 'success' | 'warning' | 'danger' | 'neutral' | 'info';
  pulse?: boolean;
  size?: 'sm' | 'md';
  className?: string;
}

export const AurixBadge: React.FC<AurixBadgeProps> = ({
  children,
  variant = 'gold',
  pulse = false,
  size = 'sm',
  className = '',
}) => {
  const getStyles = () => {
    switch (variant) {
      case 'success':
        return 'bg-[#3DDB91]/10 text-[#3DDB91] border-[#3DDB91]/30 shadow-[0_0_10px_rgba(61,219,145,0.15)]';
      case 'warning':
        return 'bg-[#F3B33D]/10 text-[#F3B33D] border-[#F3B33D]/30 shadow-[0_0_10px_rgba(243,179,61,0.15)]';
      case 'danger':
        return 'bg-[#FF6B6B]/10 text-[#FF6B6B] border-[#FF6B6B]/30 shadow-[0_0_10px_rgba(255,107,107,0.15)]';
      case 'neutral':
        return 'bg-white/[0.04] text-slate-400 border-white/[0.08]';
      case 'info':
      case 'gold':
      default:
        return 'bg-[#D4AF37]/10 text-[#D4AF37] border-[#D4AF37]/30 shadow-[0_0_12px_rgba(212,175,55,0.15)]';
    }
  };

  const sizeStyles = size === 'sm' ? 'px-2 py-0.5 text-[9px]' : 'px-2.5 py-1 text-[11px]';

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-mono font-bold uppercase tracking-wider rounded-md border ${getStyles()} ${sizeStyles} ${className}`}
    >
      {pulse && (
        <span
          className={`w-1.5 h-1.5 rounded-full animate-ping ${
            variant === 'success'
              ? 'bg-[#3DDB91]'
              : variant === 'danger'
              ? 'bg-[#FF6B6B]'
              : variant === 'warning'
              ? 'bg-[#F3B33D]'
              : 'bg-[#D4AF37]'
          }`}
        />
      )}
      {children}
    </span>
  );
};
