'use client';

import React from 'react';

export interface AurixCardProps {
  children?: React.ReactNode;
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  badge?: React.ReactNode;
  action?: React.ReactNode;
  headerAction?: React.ReactNode;
  icon?: React.ComponentType<{ className?: string }>;
  variant?: 'glass' | 'elevated' | 'interactive' | 'gold-border' | 'default';
  className?: string;
  onClick?: () => void;
}

export const AurixCard: React.FC<AurixCardProps> = ({
  children,
  title,
  subtitle,
  badge,
  action,
  headerAction,
  icon: Icon,
  variant = 'glass',
  className = '',
  onClick,
}) => {
  const getVariantStyles = () => {
    switch (variant) {
      case 'interactive':
        return 'aurix-card-glass aurix-card-interactive cursor-pointer';
      case 'elevated':
        return 'bg-[#0E1117] border border-white/[0.08] shadow-[0_12px_36px_rgba(0,0,0,0.8)]';
      case 'gold-border':
        return 'aurix-card-glass border-[#D4AF37]/40 shadow-[0_0_20px_rgba(212,175,55,0.1)]';
      case 'default':
      case 'glass':
      default:
        return 'aurix-card-glass';
    }
  };

  const hasHeader = title || subtitle || badge || action || headerAction || Icon;

  return (
    <div
      onClick={onClick}
      className={`rounded-xl p-5 relative overflow-hidden transition-all duration-300 ${getVariantStyles()} ${className}`}
    >
      {hasHeader && (
        <div className="flex items-start justify-between gap-4 mb-4 pb-3 border-b border-white/[0.06]">
          <div className="flex items-center gap-2.5 min-w-0">
            {Icon && <Icon className="w-4 h-4 text-[#D4AF37] shrink-0" />}
            <div className="min-w-0">
              {title && (
                <div className="flex items-center gap-2 flex-wrap">
                  <h3 className="text-sm font-bold text-white tracking-wide uppercase font-mono truncate">
                    {title}
                  </h3>
                  {badge && <div>{badge}</div>}
                </div>
              )}
              {subtitle && (
                <p className="text-[10px] font-mono text-slate-400 mt-0.5">
                  {subtitle}
                </p>
              )}
            </div>
          </div>
          {(action || headerAction) && (
            <div className="flex items-center gap-2 shrink-0">
              {action || headerAction}
            </div>
          )}
        </div>
      )}
      {children}
    </div>
  );
};
