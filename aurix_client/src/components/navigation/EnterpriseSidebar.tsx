'use client';

import React, { useState } from 'react';
import { createPortal } from 'react-dom';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { ApiClient } from '@/services/api/apiClient';
import { DOMAIN_REGISTRY } from '@/config/domainRegistry';
import { useAurixIntro } from '@/context/AurixIntroContext';
import {
  LayoutDashboard, Target, TestTube, Bot,
  Truck, Boxes, Factory, ShoppingCart, Share2,
  TrendingUp, Landmark,
  ShieldAlert, GitFork, Database, Sliders,
  LogOut, ShieldCheck, PanelLeftClose, PanelLeftOpen, ChevronRight
} from 'lucide-react';

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  tag?: string;
  badgeVariant?: 'danger' | 'warning' | 'gold';
}

interface NavSection {
  title: string;
  items: NavItem[];
}

const NAVIGATION_SECTIONS: NavSection[] = [
  {
    title: 'EXECUTIVE COMMAND',
    items: [
      { name: 'Overview', href: '/', icon: LayoutDashboard, tag: '01' },
      { name: 'Decisions', href: '/decisions', icon: Target, tag: '02' },
      { name: 'Scenarios', href: '/scenarios', icon: TestTube, tag: '03' },
      { name: 'Agents & Studio', href: '/agent-studio', icon: Bot, tag: '04', badgeVariant: 'gold' },
    ],
  },
  {
    title: 'SUPPLY CHAIN & LOGISTICS',
    items: [
      { name: 'Supply Chain', href: '/supply-chain', icon: Truck, tag: '05' },
      { name: 'Inventory', href: '/inventory', icon: Boxes, tag: '06' },
      { name: 'Manufacturing', href: '/manufacturing', icon: Factory, tag: '07' },
      { name: 'Procurement', href: '/procurement', icon: ShoppingCart, tag: '08' },
      { name: 'Logistics', href: '/logistics', icon: Share2, tag: '09' },
    ],
  },
  {
    title: 'COMMERCIAL & FINANCE',
    items: [
      { name: 'Sales', href: '/sales', icon: TrendingUp, tag: '10' },
      { name: 'Finance', href: '/finance', icon: Landmark, tag: '11' },
    ],
  },
  {
    title: 'INTELLIGENCE & MLOPS',
    items: [
      { name: 'Risk & Assurance', href: '/risk-assurance', icon: ShieldAlert, tag: '12', badgeVariant: 'danger' },
      { name: 'Processes', href: '/processes', icon: GitFork, tag: '13' },
      { name: 'Data & Intake', href: '/data-integrations', icon: Database, tag: '14' },
      { name: 'Admin & Control', href: '/admin', icon: Sliders, tag: '15' },
    ],
  },
];

export const EnterpriseSidebar: React.FC<{
  isCollapsed?: boolean;
  onToggle?: () => void;
}> = ({ isCollapsed = false, onToggle }) => {
  const pathname = usePathname();
  const router = useRouter();
  const [flyoutHref, setFlyoutHref] = useState<string | null>(null);
  const [flyoutRect, setFlyoutRect] = useState<{ top: number; left: number } | null>(null);
  const { phase, navLogoRef } = useAurixIntro();


  // Build a route -> subdomain list lookup so the sidebar can surface
  // subdomain discovery on hover, without permanently listing everything.
  const domainByRoute = React.useMemo(() => {
    const map = new Map<string, (typeof DOMAIN_REGISTRY)[string]>();
    Object.values(DOMAIN_REGISTRY).forEach((domain) => {
      map.set(domain.route, domain);
    });
    return map;
  }, []);

  const handleLogout = () => {
    ApiClient.clearAuth();
    router.push('/login');
  };

  const handleNavClick = (isActive: boolean) => {
    if (isActive && onToggle) onToggle();
  };

  const asideClass = `w-${isCollapsed ? '20' : '64'} bg-[#07090D] border-r border-white/[0.08] fixed top-0 left-0 bottom-0 z-50 flex flex-col justify-between font-mono select-none transition-all duration-300 ease-in-out`;

  return (
    <aside aria-label="Enterprise Navigation Drawer" className={asideClass}>
      <div className={`h-[4.25rem] ${isCollapsed ? 'px-3 justify-center' : 'px-6 justify-between'} flex items-center border-b border-white/[0.08] bg-[#030303]/60`}>
        <Link
          href="/"
          prefetch={true}
          ref={navLogoRef}
          style={{
            opacity: phase === 'complete' ? 1 : 0,
            transition: 'opacity 180ms ease',
          }}
          aria-hidden={phase !== 'complete'}
          onClick={() => handleNavClick(pathname === '/')}
          className="flex items-center gap-3 group"
        >
          <div className="w-7 h-7 shrink-0 flex items-center justify-center">
            <svg viewBox="0 0 100 100" className="w-7 h-7 fill-none">
              <path d="M 50 14 L 84 76 L 70 76 L 50 38 L 30 76 L 16 76 Z" fill="#D4AF37" />
              <polygon points="50,44 62,66 50,74 38,66" fill="#07090D" stroke="#D4AF37" strokeWidth="1.5" />
              <circle cx="50" cy="62" r="3.5" fill="#D4AF37" />
            </svg>
          </div>

          {!isCollapsed && (
            <div className="flex flex-col min-w-0">
              <span className="text-white font-bold tracking-[0.25em] text-base group-hover:text-[#D4AF37] transition-colors truncate">
                AURIX AI
              </span>
              <span className="text-[#D4AF37] text-[8px] tracking-[0.3em] uppercase font-bold truncate">
                ENTERPRISE ENGINE
              </span>
            </div>
          )}
        </Link>

        {!isCollapsed && (
          <span className="w-2 h-2 rounded-full bg-[#3DDB91] animate-pulse shrink-0 shadow-[0_0_8px_rgba(61,219,145,0.8)]" title="System Operational" />
        )}
      </div>

      <nav className="flex-1 overflow-y-auto px-2.5 py-4 space-y-5 scrollbar-thin scrollbar-thumb-white/10">
        {NAVIGATION_SECTIONS.map((section) => (
          <div key={section.title} className="space-y-1">
            {!isCollapsed ? (
              <span className="px-3 text-[9px] font-bold text-slate-500 uppercase tracking-widest block mb-2">
                {section.title}
              </span>
            ) : (
              <div className="border-t border-white/[0.06] my-2 mx-1" />
            )}

            {section.items.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href));
              const domain = domainByRoute.get(item.href);
              const hasSubdomains = !isCollapsed && domain && domain.subdomains.length > 0;
              const isFlyoutOpen = flyoutHref === item.href;

              return (
                <div
                  key={item.href}
                  className="relative"
                  onMouseEnter={(e) => {
                    if (!hasSubdomains) return;
                    const r = e.currentTarget.getBoundingClientRect();
                    setFlyoutRect({ top: r.top, left: r.right });
                    setFlyoutHref(item.href);
                  }}
                  onMouseLeave={() => setFlyoutHref((cur) => (cur === item.href ? null : cur))}
                  onFocus={(e) => {
                    if (!hasSubdomains) return;
                    const r = e.currentTarget.getBoundingClientRect();
                    setFlyoutRect({ top: r.top, left: r.right });
                    setFlyoutHref(item.href);
                  }}
                  onBlur={(e) => {
                    if (!e.currentTarget.contains(e.relatedTarget as Node)) {
                      setFlyoutHref((cur) => (cur === item.href ? null : cur));
                    }
                  }}
                >
                  <Link
                    href={item.href}
                    prefetch={true}
                    onClick={() => handleNavClick(isActive)}
                    title={isCollapsed ? `${item.name} (${section.title})` : undefined}
                    className={`flex items-center ${
                      isCollapsed ? 'justify-center px-2' : 'justify-between px-3'
                    } py-2 rounded-lg text-xs transition-all group relative ${
                      isActive
                        ? 'bg-[#D4AF37]/[0.12] text-white font-bold border border-[#D4AF37]/30 shadow-[0_0_12px_rgba(212,175,55,0.12)]'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]'
                    }`}
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <Icon
                        className={`w-4 h-4 shrink-0 transition-colors ${
                          isActive ? 'text-[#D4AF37]' : 'text-slate-500 group-hover:text-slate-300'
                        }`}
                      />
                      {!isCollapsed && <span className="truncate">{item.name}</span>}
                    </div>

                    {!isCollapsed && (
                      <div className="flex items-center gap-1.5 shrink-0">
                        {item.badgeVariant === 'danger' && <span className="w-1.5 h-1.5 rounded-full bg-[#FF6B6B] animate-pulse" />}
                        {item.badgeVariant === 'gold' && <span className="w-1.5 h-1.5 rounded-full bg-[#D4AF37]" />}

                        {hasSubdomains && (
                          <ChevronRight
                            className={`w-3 h-3 text-slate-600 transition-transform duration-200 ${isFlyoutOpen ? 'rotate-90 text-[#D4AF37]' : ''}`}
                          />
                        )}

                        {item.tag && !hasSubdomains && (
                          <span
                            className={`text-[9px] px-1.5 py-0.5 rounded font-mono ${
                              isActive
                                ? 'bg-[#D4AF37]/20 text-[#D4AF37] font-bold'
                                : item.badgeVariant === 'danger'
                                ? 'bg-[#FF6B6B]/15 text-[#FF8585] font-bold'
                                : 'bg-white/[0.04] text-slate-500 group-hover:text-slate-400'
                            }`}
                          >
                            {item.tag}
                          </span>
                        )}
                      </div>
                    )}

                    {isCollapsed && isActive && (
                      <span className="absolute right-0 top-2 bottom-2 w-1 rounded-l bg-[#D4AF37]" />
                    )}
                  </Link>

                  {hasSubdomains && isFlyoutOpen && domain && flyoutRect && typeof document !== 'undefined' &&
                    createPortal(
                      <div
                        className="fixed w-72 z-[70] rounded-xl border border-[#D4AF37]/20 bg-[#0C0E12] shadow-[0_8px_32px_rgba(0,0,0,0.6)] p-2 animate-pure-fade"
                        style={{ top: flyoutRect.top, left: flyoutRect.left + 8 }}
                        role="menu"
                        onMouseEnter={() => setFlyoutHref(item.href)}
                        onMouseLeave={() => setFlyoutHref((cur) => (cur === item.href ? null : cur))}
                      >
                        <div className="px-2.5 py-1.5 mb-1 border-b border-white/[0.06]">
                          <span className="text-[9px] font-bold text-[#D4AF37] uppercase tracking-widest">
                            {domain.title} Ã¢â‚¬â€ Subdomains
                          </span>
                        </div>
                        {domain.subdomains.map((sub) => {
                          const href = sub.route || `${item.href}?subdomain=${sub.id}`;
                          return (
                            <Link
                              key={sub.id}
                              href={href}
                              prefetch={false}
                              onClick={() => setFlyoutHref(null)}
                              className="flex items-start gap-2.5 px-2.5 py-2 rounded-lg hover:bg-white/[0.05] transition-colors group/sub"
                              role="menuitem"
                            >
                              {sub.icon && (
                                <sub.icon className="w-3.5 h-3.5 text-slate-500 group-hover/sub:text-[#D4AF37] shrink-0 mt-0.5 transition-colors" />
                              )}
                              <div className="min-w-0">
                                <div className="text-[11px] text-slate-200 font-bold group-hover/sub:text-white truncate">
                                  {sub.title}
                                </div>
                                <div className="text-[10px] text-slate-500 leading-snug line-clamp-2">
                                  {sub.description}
                                </div>
                              </div>
                            </Link>
                          );
                        })}
                      </div>,
                      document.body
                    )}
                </div>
              );
            })}
          </div>
        ))}
      </nav>

      <div className="px-3 py-2 border-t border-white/[0.06] bg-[#07090D] flex items-center justify-between">
        <button
          onClick={onToggle}
          title={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
          className={`w-full flex items-center ${
            isCollapsed ? 'justify-center' : 'justify-between px-2'
          } py-1.5 rounded-lg bg-white/[0.03] hover:bg-white/[0.07] text-slate-400 hover:text-white transition-colors cursor-pointer border border-white/[0.05]`}
        >
          {!isCollapsed && <span className="text-[10px] font-bold tracking-wider uppercase">COLLAPSE MENU</span>}
          {isCollapsed ? <PanelLeftOpen className="w-4 h-4 text-[#D4AF37]" /> : <PanelLeftClose className="w-4 h-4 text-slate-400" />}
        </button>
      </div>

      <div className={`p-3 border-t border-white/[0.08] bg-[#030303] ${isCollapsed ? 'flex flex-col items-center' : 'space-y-2'}`}>
        {!isCollapsed ? (
          <>
            <div className="p-2 rounded-lg bg-white/[0.02] border border-white/[0.05] flex items-center justify-between">
              <div className="flex flex-col min-w-0">
                <span className="text-[10px] text-white font-bold truncate">System Operator</span>
                <span className="text-[9px] text-[#D4AF37] truncate">EXECUTIVE LEVEL</span>
              </div>
              <button onClick={handleLogout} className="p-1.5 rounded text-slate-500 hover:text-[#FF8585] hover:bg-white/[0.05] transition-colors cursor-pointer">
                <LogOut className="w-3.5 h-3.5" />
              </button>
            </div>
            <div className="px-2 flex items-center justify-between text-[9px] text-slate-500">
              <span className="flex items-center gap-1">
                <ShieldCheck className="w-3 h-3 text-[#3DDB91]" />
                <span>RLS ISOLATION</span>
              </span>
              <span className="text-[#3DDB91] font-bold">ENFORCED</span>
            </div>
          </>
        ) : (
          <button onClick={handleLogout} className="p-2 rounded-lg bg-white/[0.02] border border-white/[0.05] text-slate-400 hover:text-[#FF8585] transition-colors cursor-pointer">
            <LogOut className="w-4 h-4" />
          </button>
        )}
      </div>
    </aside>
  );
};

