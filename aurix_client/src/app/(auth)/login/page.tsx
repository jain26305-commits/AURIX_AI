'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { AurixLogoMark } from '@/components/brand/AurixLogoMark';
import { AurixButton } from '@/components/ui/AurixButton';
import { useTenant } from '@/context/TenantContext';
import { ShieldCheck, Lock, User, Building, AlertCircle } from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const { login } = useTenant();
  const [tenantId, setTenantId] = useState('ENTERPRISE_GLOBAL');
  const [email, setEmail] = useState('executive@aurix.ai');
  const [password, setPassword] = useState('••••••••••••');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg(null);

    try {
      await login({ email, password, tenantId });
      router.push('/control-tower');
    } catch (err: unknown) {
      setErrorMsg((err as Error)?.message || 'Authentication failed. Please verify your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="aurix-card-glass rounded-2xl p-8 border border-white/[0.08] shadow-2xl relative overflow-hidden space-y-6 select-none">
      <div className="absolute inset-x-0 top-0 h-[2px] bg-gradient-to-r from-transparent via-[#D4AF37] to-transparent" />

      <div className="text-center flex flex-col items-center space-y-2">
        <AurixLogoMark idPrefix="login" iconClassName="w-10 h-10" textClassName="text-2xl" />
        <span className="text-[10px] font-mono tracking-[0.3em] uppercase text-gold font-bold">
          DETERMINISTIC DECISION PLATFORM
        </span>
      </div>

      {errorMsg && (
        <div className="p-3 rounded-lg bg-[#FF6B6B]/10 border border-[#FF6B6B]/30 flex items-center gap-2 text-xs font-mono text-[#FF8585]">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      <form onSubmit={handleLogin} className="space-y-4 text-xs font-mono">
        <div className="space-y-1">
          <label className="text-slate-400 text-[10px] uppercase font-bold flex items-center gap-1.5">
            <Building className="w-3 h-3 text-[#D4AF37]" /> TENANT IDENTIFIER
          </label>
          <input
            type="text"
            value={tenantId}
            onChange={(e) => setTenantId(e.target.value)}
            className="w-full bg-[#15171A] border border-white/10 rounded-lg px-3 py-2 text-white font-mono focus:border-[#D4AF37] focus:outline-none"
            required
          />
        </div>

        <div className="space-y-1">
          <label className="text-slate-400 text-[10px] uppercase font-bold flex items-center gap-1.5">
            <User className="w-3 h-3 text-gold" /> OPERATOR EMAIL
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full bg-[#15171A] border border-white/10 rounded-lg px-3 py-2 text-white font-mono focus:border-[#D4AF37] focus:outline-none"
            required
          />
        </div>

        <div className="space-y-1">
          <label className="text-slate-400 text-[10px] uppercase font-bold flex items-center gap-1.5">
            <Lock className="w-3 h-3 text-slate-400" /> SECURE CREDENTIAL
          </label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full bg-[#15171A] border border-white/10 rounded-lg px-3 py-2 text-white font-mono focus:border-[#D4AF37] focus:outline-none"
            required
          />
        </div>

        <div className="pt-2">
          <AurixButton variant="gold" size="md" className="w-full" loading={isLoading} type="submit">
            <ShieldCheck className="w-4 h-4 mr-1.5" />
            <span>AUTHENTICATE & ENTER</span>
          </AurixButton>
        </div>
      </form>

      <div className="text-center pt-2 border-t border-white/[0.04] text-[10px] font-mono text-slate-500">
        RLS ENCRYPTED • ENTERPRISE GOVERNANCE PROTECTED
      </div>
    </div>
  );
}