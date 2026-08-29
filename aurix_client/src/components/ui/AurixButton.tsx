'use client';

import React from 'react';
import { Loader2 } from 'lucide-react';

export interface AurixButtonProps {
  children: React.ReactNode;
  variant?: 'gold' | 'glass' | 'secondary' | 'danger' | 'primary' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  icon?: React.ComponentType<{ className?: string }>;
  loading?: boolean;
  disabled?: boolean;
  onClick?: () => void;
  className?: string;
  type?: 'button' | 'submit' | 'reset';
}

export const AurixButton: React.FC<AurixButtonProps> = ({
  children,
  variant = 'gold',
  size = 'md',
  icon: Icon,
  loading = false,
  disabled = false,
  onClick,
  className = '',
  type = 'button',
}) => {
  const getVariantStyles = () => {
    switch (variant) {
      case 'secondary':
      case 'glass':
        return 'bg-white/[0.04] hover:bg-white/[0.08] text-white border border-white/[0.1] hover:border-[#D4AF37]/40';
      case 'ghost':
        return 'bg-transparent text-slate-400 hover:text-white hover:bg-white/[0.04]';
      case 'danger':
        return 'bg-[#FF6B6B]/15 hover:bg-[#FF6B6B]/25 text-[#FF8585] border border-[#FF6B6B]/40';
      case 'primary':
      case 'gold':
      default:
        return 'bg-gradient-to-r from-[#D4AF37] via-[#F0D878] to-[#D4AF37] text-black font-extrabold shadow-[0_0_20px_rgba(212,175,55,0.3)] hover:shadow-[0_0_30px_rgba(212,175,55,0.5)] border border-[#F0D878]/50';
    }
  };

  const getSizeStyles = () => {
    switch (size) {
      case 'sm':
        return 'px-3 py-1.5 text-xs';
      case 'lg':
        return 'px-6 py-3 text-sm';
      case 'md':
      default:
        return 'px-4 py-2 text-xs';
    }
  };

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className={`inline-flex items-center justify-center gap-2 rounded-lg font-mono uppercase tracking-wider transition-all duration-200 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed ${getVariantStyles()} ${getSizeStyles()} ${className}`}
    >
      {loading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
      {!loading && Icon && <Icon className="w-3.5 h-3.5" />}
      <span>{children}</span>
    </button>
  );
};
