'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Search, X, ArrowRight } from 'lucide-react';
import { DOMAIN_REGISTRY } from '@/config/domainRegistry';

export interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({ isOpen, onClose }) => {
  const [query, setQuery] = useState('');
  const router = useRouter();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const filteredDomains = Object.values(DOMAIN_REGISTRY).filter(
    (d) =>
      d.title.toLowerCase().includes(query.toLowerCase()) ||
      d.subdomains.some((s) => s.title.toLowerCase().includes(query.toLowerCase()))
  );

  const navigateTo = (route: string) => {
    router.push(route);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 px-4 bg-black/80 backdrop-blur-md animate-pure-fade">
      <div className="w-full max-w-2xl aurix-card-glass border-[#D4AF37]/30 shadow-[0_0_50px_rgba(0,0,0,0.9)] rounded-2xl overflow-hidden">
        <div className="p-4 border-b border-white/[0.08] flex items-center gap-3">
          <Search className="w-4 h-4 text-[#D4AF37]" />
          <input
            autoFocus
            type="text"
            placeholder="Type a command, domain, or subdomain..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full bg-transparent text-white font-mono text-sm focus:outline-none placeholder-slate-500"
          />
          <button onClick={onClose} className="text-slate-500 hover:text-white p-1">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="max-h-96 overflow-y-auto p-3 space-y-4 font-mono text-xs">
          {filteredDomains.length === 0 ? (
            <div className="p-8 text-center text-slate-500">NO DOMAINS OR WORKSPACES MATCHED</div>
          ) : (
            filteredDomains.map((domain) => {
              const Icon = domain.icon;
              return (
                <div key={domain.id} className="space-y-1.5">
                  <div
                    onClick={() => navigateTo(domain.route)}
                    className="flex items-center justify-between p-2.5 rounded-lg bg-white/[0.02] hover:bg-[#D4AF37]/10 hover:border-[#D4AF37]/30 border border-transparent cursor-pointer group transition-all"
                  >
                    <div className="flex items-center gap-2.5">
                      <Icon className="w-4 h-4 text-[#D4AF37]" />
                      <span className="font-bold text-white uppercase">{domain.title}</span>
                    </div>
                    <span className="text-[10px] text-slate-500 group-hover:text-[#D4AF37]">OPEN DOMAIN &rarr;</span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 pl-6">
                    {domain.subdomains.map((sub) => (
                      <div
                        key={sub.id}
                        onClick={() => navigateTo(`${domain.route}?subdomain=${sub.id}`)}
                        className="p-2 rounded bg-white/[0.01] hover:bg-white/[0.04] text-slate-400 hover:text-white cursor-pointer flex items-center justify-between transition-colors border border-white/[0.02]"
                      >
                        <span className="truncate">{sub.title}</span>
                        <ArrowRight className="w-3 h-3 text-slate-600 shrink-0" />
                      </div>
                    ))}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
