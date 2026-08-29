'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { ArrowRight, Layers, Lock } from 'lucide-react';
import { AurixBadge } from '@/components/ui/AurixBadge';

export interface SubdomainItem {
  id: string;
  title: string;
  description: string;
  metric?: string;
  metricLabel?: string;
  badge?: string;
  badgeVariant?: 'gold' | 'success' | 'warning' | 'danger' | 'info';
  icon?: React.ComponentType<{ className?: string }>;
  disabled?: boolean;
  /** If set, selecting this subdomain navigates to a dedicated route instead of
   *  switching in-place workspace state within the domain orchestrator. */
  route?: string;
}

export interface SubdomainWorkspaceSelectorProps {
  subdomains: SubdomainItem[];
  activeSubdomainId?: string | null;
  onSelectSubdomain: (id: string) => void;
}

export const SubdomainWorkspaceSelector: React.FC<SubdomainWorkspaceSelectorProps> = ({
  subdomains,
  activeSubdomainId,
  onSelectSubdomain,
}) => {
  const router = useRouter();

  const handleSelect = (item: SubdomainItem) => {
    if (item.disabled) return;
    if (item.route) {
      router.push(item.route);
      return;
    }
    onSelectSubdomain(item.id);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between border-b border-white/[0.06] pb-3">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-[#D4AF37]" />
          <h2 className="text-xs font-mono font-bold tracking-[0.2em] text-white uppercase">
            ACTIVE WORKSPACE MODULES
          </h2>
        </div>
        <span className="text-[10px] font-mono text-slate-500 uppercase tracking-widest hidden sm:inline-block">
          SELECT SUBDOMAIN TO ENTER PRIMARY WORKSPACE
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {subdomains.map((item) => {
          const isSelected = activeSubdomainId === item.id;
          const Icon = item.icon;

          return (
            <div
              key={item.id}
              onClick={() => handleSelect(item)}
              className={`p-5 rounded-xl cursor-pointer select-none transition-all duration-300 relative overflow-hidden group ${
                isSelected
                  ? 'bg-[#14171E] border-2 border-[#D4AF37] shadow-[0_0_30px_rgba(212,175,55,0.25)] -translate-y-0.5'
                  : item.disabled
                  ? 'bg-white/[0.01] border border-white/[0.04] opacity-50 cursor-not-allowed'
                  : 'aurix-card-glass hover:border-[#D4AF37]/40 hover:bg-white/[0.04] hover:-translate-y-1'
              }`}
            >
              {isSelected && (
                <div className="absolute top-0 right-0 w-24 h-24 bg-[radial-gradient(circle_at_top_right,rgba(212,175,55,0.2)_0%,transparent_70%)] pointer-events-none" />
              )}

              <div className="flex items-start justify-between gap-3 mb-3">
                <div className="flex items-center gap-2.5 min-w-0">
                  {Icon && (
                    <div
                      className={`p-2 rounded-lg transition-colors ${
                        isSelected
                          ? 'bg-[#D4AF37]/20 text-[#D4AF37]'
                          : 'bg-white/[0.04] text-slate-400 group-hover:text-[#D4AF37] group-hover:bg-[#D4AF37]/10'
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                    </div>
                  )}
                  <div className="min-w-0">
                    <h3 className="text-sm font-bold text-white tracking-wide uppercase font-mono truncate group-hover:text-[#D4AF37] transition-colors">
                      {item.title}
                    </h3>
                    {item.badge && (
                      <AurixBadge
                        variant={item.badgeVariant || 'gold'}
                        size="sm"
                        className="mt-1"
                      >
                        {item.badge}
                      </AurixBadge>
                    )}
                  </div>
                </div>

                {item.disabled ? (
                  <Lock className="w-4 h-4 text-slate-600 shrink-0" />
                ) : (
                  <ArrowRight
                    className={`w-4 h-4 shrink-0 transition-transform ${
                      isSelected
                        ? 'text-[#D4AF37] translate-x-1'
                        : 'text-slate-600 group-hover:text-white group-hover:translate-x-1'
                    }`}
                  />
                )}
              </div>

              <p className="text-xs text-slate-400 font-sans line-clamp-2 mb-4 leading-relaxed">
                {item.description}
              </p>

              {item.metric && (
                <div className="pt-3 border-t border-white/[0.05] flex items-center justify-between font-mono">
                  <span className="text-[10px] text-slate-500 uppercase tracking-wider">
                    {item.metricLabel || 'KEY TELEMETRY'}
                  </span>
                  <span className="text-xs font-bold text-white tracking-wider group-hover:text-[#D4AF37] transition-colors">
                    {item.metric}
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
