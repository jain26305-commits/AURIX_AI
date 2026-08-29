'use client';

import React from 'react';
import { CryptographicExecutionToken } from '@/types/action.types';
import { AurixButton } from '@/components/ui/AurixButton';
import { X, FileKey, Copy, Check } from 'lucide-react';

interface ExecutionTokenModalProps {
  token: CryptographicExecutionToken | undefined;
  isOpen: boolean;
  onClose: () => void;
}

export const ExecutionTokenModal: React.FC<ExecutionTokenModalProps> = ({
  token,
  isOpen,
  onClose,
}) => {
  const [copied, setCopied] = React.useState(false);
  if (!isOpen || !token) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(token, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md select-none font-mono">
      <div className="w-full max-w-lg aurix-card-glass bg-[#0C0E12] border border-gold/30 rounded-2xl p-6 shadow-2xl space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-white/[0.08]">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <FileKey className="w-4 h-4 text-gold" />
            PHASE 14 EXECUTION TOKEN
          </h3>
          <button onClick={onClose} className="p-1 rounded text-slate-400 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="space-y-3 text-xs">
          <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06] space-y-2 text-slate-300">
            <div className="flex justify-between">
              <span className="text-slate-500">TOKEN ID:</span>
              <span className="text-gold font-bold">{token.tokenId}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">AUTHORIZATION:</span>
              <span className="text-white font-bold">{token.phase14AuthorizationCode}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">SIGNED BY:</span>
              <span className="text-white">{token.signedBy} ({token.role})</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">TIMESTAMP:</span>
              <span className="text-slate-400">{token.timestamp}</span>
            </div>
          </div>

          <div className="space-y-1">
            <span className="text-[10px] text-slate-500 uppercase font-bold">SHA-256 PROVENANCE CHECKSUM</span>
            <div className="p-3 rounded-lg bg-black/60 border border-white/10 text-[10px] text-slate-300 break-all">
              {token.sha256Checksum}
            </div>
          </div>
        </div>

        <div className="pt-3 border-t border-white/[0.06] flex items-center justify-end gap-3">
          <AurixButton variant="secondary" size="sm" onClick={handleCopy}>
            {copied ? <Check className="w-3.5 h-3.5 mr-1" /> : <Copy className="w-3.5 h-3.5 mr-1" />}
            <span>{copied ? 'COPIED JSON' : 'COPY TOKEN'}</span>
          </AurixButton>
          <AurixButton variant="gold" size="sm" onClick={onClose}>
            CLOSE
          </AurixButton>
        </div>
      </div>
    </div>
  );
};