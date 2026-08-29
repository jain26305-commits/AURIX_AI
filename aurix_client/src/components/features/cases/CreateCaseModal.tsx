'use client';

import React, { useState } from 'react';
import { OperationalCase, CasePriority } from '@/types/case.types';
import { AurixButton } from '@/components/ui/AurixButton';
import { X, FolderPlus } from 'lucide-react';

interface CreateCaseModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (newCase: Partial<OperationalCase>) => void;
}

export const CreateCaseModal: React.FC<CreateCaseModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
}) => {
  const [title, setTitle] = useState('');
  const [domain, setDomain] = useState('Inventory Risk');
  const [priority, setPriority] = useState<CasePriority>('HIGH');
  const targetEntityId = 'SKU-001';
  const targetEntityName = '101 Beige-L (T-Shirt)';
  const [summary, setSummary] = useState('');

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      title,
      domain,
      priority,
      targetEntityId,
      targetEntityName,
      summary,
      exposureINR: 75000,
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md select-none font-mono">
      <div className="w-full max-w-lg aurix-card-glass bg-[#0C0E12] border border-gold/30 rounded-2xl p-6 shadow-2xl space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-white/[0.08]">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <FolderPlus className="w-4 h-4 text-gold" />
            PROVISION OPERATIONAL CASE
          </h3>
          <button onClick={onClose} className="p-1 rounded text-slate-400 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3.5 text-xs">
          <div className="space-y-1">
            <label className="text-slate-400 text-[10px] uppercase font-bold">CASE TITLE</label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Lead-Time Variance Remediation"
              className="w-full bg-[#15171A] border border-white/10 rounded-lg px-3 py-2 text-white focus:border-[#D4AF37] focus:outline-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-slate-400 text-[10px] uppercase font-bold">DOMAIN</label>
              <select
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
                className="w-full bg-[#15171A] border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none"
              >
                <option value="Inventory Risk">Inventory Risk</option>
                <option value="Logistics">Logistics</option>
                <option value="Supplier Reliability">Supplier Reliability</option>
                <option value="Demand Shift">Demand Shift</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-slate-400 text-[10px] uppercase font-bold">PRIORITY</label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value as CasePriority)}
                className="w-full bg-[#15171A] border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none"
              >
                <option value="CRITICAL">CRITICAL</option>
                <option value="HIGH">HIGH</option>
                <option value="MEDIUM">MEDIUM</option>
                <option value="LOW">LOW</option>
              </select>
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-slate-400 text-[10px] uppercase font-bold">INCIDENT SUMMARY</label>
            <textarea
              required
              rows={3}
              value={summary}
              onChange={(e) => setSummary(e.target.value)}
              placeholder="Describe operational anomaly and business impact..."
              className="w-full bg-[#15171A] border border-white/10 rounded-lg px-3 py-2 text-white focus:border-[#D4AF37] focus:outline-none resize-none"
            />
          </div>

          <div className="pt-3 border-t border-white/[0.06] flex items-center justify-end gap-3">
            <AurixButton variant="ghost" size="sm" onClick={onClose} type="button">
              CANCEL
            </AurixButton>
            <AurixButton variant="gold" size="md" type="submit">
              PROVISION CASE
            </AurixButton>
          </div>
        </form>
      </div>
    </div>
  );
};