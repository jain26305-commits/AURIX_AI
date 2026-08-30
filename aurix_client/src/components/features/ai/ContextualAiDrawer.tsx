'use client';

import React from 'react';
import { AiQueryResponse } from '@/types/ai-query.types';
import { BusinessInsight, ProvenanceMetadata } from '@/types/api.types';
import { AurixButton } from '@/components/ui/AurixButton';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { ProvenancePopover } from '@/components/trust/ProvenancePopover';
import {
  X,
  Sparkles,
  Send,
  Cpu,
  ArrowRight,
  AlertCircle,
} from 'lucide-react';

export interface ContextualAiDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  queryText: string;
  onQueryTextChange: (text: string) => void;
  onSubmitQuery: (customText?: string) => void;
  queryHistory: AiQueryResponse[];
  isLoading: boolean;
  error?: { code: string; message: string; statusCode?: number } | null;
  workspaceTitle: string;
  activeInsight?: BusinessInsight;
  provenance?: ProvenanceMetadata;
}

export const ContextualAiDrawer: React.FC<ContextualAiDrawerProps> = ({
  isOpen,
  onClose,
  queryText,
  onQueryTextChange,
  onSubmitQuery,
  queryHistory,
  isLoading,
  error,
  workspaceTitle,
  activeInsight,
  provenance,
}) => {
  if (!isOpen) return null;

  const quickPrompts = [
    'Why is this entity flagged for review?',
    'What is the projected financial impact if unaddressed?',
    'Provide quantitative trade-offs for recommended countermeasure',
  ];

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/65 backdrop-blur-sm animate-pure-fade select-none font-mono">
      <div className="w-full max-w-lg bg-[#0C0E12] border-l border-white/10 h-full p-6 flex flex-col justify-between space-y-4">
        <div className="flex items-center justify-between pb-4 border-b border-white/10 shrink-0">
          <div>
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-[#D4AF37] animate-pulse" />
              <h3 className="text-sm font-bold text-white tracking-wide uppercase">
                AURIX CONTEXTUAL AI
              </h3>
            </div>

            <div className="flex items-center gap-2 mt-1">
              <span className="text-[10px] text-slate-400 block">
                Context:{' '}
                <strong className="text-[#D4AF37]">
                  {workspaceTitle}
                </strong>
              </span>
              {provenance && <ProvenancePopover details={provenance} />}
            </div>
          </div>

          <button
            onClick={onClose}
            aria-label="Close AURIX AI"
            className="p-1.5 rounded-lg bg-white/[0.05] hover:bg-white/10 text-slate-400 hover:text-white cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {activeInsight && (
          <div className="p-3 rounded-lg bg-[#D4AF37]/[0.04] border border-[#D4AF37]/30 space-y-1.5 shrink-0 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-[9px] font-bold text-[#D4AF37] uppercase tracking-wider flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                ACTIVE WORKBENCH ANCHOR
              </span>

              <AurixBadge
                variant={
                  activeInsight.severity === 'CRITICAL'
                    ? 'danger'
                    : 'gold'
                }
                size="sm"
              >
                {activeInsight.type}
              </AurixBadge>
            </div>

            <h4 className="text-white font-bold">
              {activeInsight.title}
            </h4>

            <p className="text-slate-400 text-[11px] font-sans leading-relaxed">
              {activeInsight.description}
            </p>

            {activeInsight.quantitativeImpact && (
              <div className="pt-1 text-[10px] text-slate-300 font-mono">
                <span className="text-slate-500">IMPACT: </span>
                <span className="text-white font-bold">
                  {activeInsight.quantitativeImpact}
                </span>
              </div>
            )}
          </div>
        )}

        <div className="flex-1 overflow-y-auto space-y-4 pr-1">
          {queryHistory.length === 0 ? (
            <div className="py-8 text-center space-y-4">
              <Sparkles className="w-8 h-8 text-[#D4AF37]/60 mx-auto" />

              <div className="space-y-1">
                <span className="text-white font-bold text-xs block uppercase">
                  DETERMINISTIC REASONING GATEWAY
                </span>

                <p className="text-slate-400 text-[11px] max-w-xs mx-auto font-sans">
                  Ask grounded questions regarding root-cause drivers,
                  SLA variances, trade-off frontiers, or financial drag.
                </p>
              </div>

              <div className="space-y-2 pt-2">
                <span className="text-[9px] text-slate-500 uppercase font-bold block">
                  ANCHORED QUERIES
                </span>

                {quickPrompts.map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => onSubmitQuery(prompt)}
                    className="w-full text-left p-2.5 rounded-lg bg-white/[0.02] border border-white/[0.06] hover:border-[#D4AF37]/40 text-slate-300 text-[11px] transition-colors cursor-pointer flex items-center justify-between group"
                  >
                    <span className="group-hover:text-white transition-colors">
                      {prompt}
                    </span>

                    <ArrowRight className="w-3 h-3 text-[#D4AF37] shrink-0" />
                  </button>
                ))}
              </div>
            </div>
          ) : (
            queryHistory.map((query) => (
              <div
                key={query.response_id}
                className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.08] space-y-3 text-xs"
              >
                <div className="flex items-center justify-between pb-2 border-b border-white/[0.04]">
                  <AurixBadge variant="gold">
                    {query.response_type.replace(/_/g, ' ')}
                  </AurixBadge>

                  <span className="text-slate-500 text-[10px]">
                    {query.evidence_quality}
                  </span>
                </div>

                <h4 className="text-white font-semibold">
                  {query.headline}
                </h4>

                <p className="text-slate-200 leading-relaxed font-sans text-xs">
                  {query.explanation ||
                    query.response ||
                    query.summary ||
                    'No explanation was returned.'}
                </p>

                {query.verified_facts.length > 0 && (
                  <div className="space-y-1.5 pt-2 border-t border-white/[0.04]">
                    <span className="text-[9px] text-[#D4AF37] uppercase font-bold flex items-center gap-1">
                      <Cpu className="w-3 h-3" />
                      VERIFIED FACTS
                    </span>

                    {query.verified_facts.map(
                      (fact: string, index: number) => (
                        <div
                          key={index}
                          className="p-2 rounded bg-black/40 border border-white/5 text-[10px] text-slate-400"
                        >
                          {fact}
                        </div>
                      ),
                    )}
                  </div>
                )}

                {query.recommendations.length > 0 && (
                  <div className="space-y-1.5 pt-2 border-t border-white/[0.04]">
                    <span className="text-[9px] text-[#D4AF37] uppercase font-bold">
                      RECOMMENDATIONS
                    </span>

                    {query.recommendations.map(
                      (recommendation: string, index: number) => (
                        <div
                          key={index}
                          className="p-2 rounded bg-black/40 border border-white/5 text-[10px] text-slate-400"
                        >
                          {recommendation}
                        </div>
                      ),
                    )}
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        <div className="pt-3 border-t border-white/10 shrink-0">
          {error && (
            <div
              role="alert"
              className="rounded-xl border border-red-400/30 bg-red-500/[0.08] p-3 text-xs text-red-200"
            >
              <div className="font-bold uppercase tracking-wider text-[10px] mb-1">
                AURIX AI REQUEST FAILED
              </div>
              <div className="font-sans leading-relaxed">
                {error.message}
              </div>
              <button
                type="button"
                onClick={() => onSubmitQuery()}
                disabled={isLoading || !queryText.trim()}
                className="mt-2 px-3 py-1.5 rounded-lg border border-red-300/30 bg-red-400/10 hover:bg-red-400/20 disabled:opacity-40 text-[10px] font-bold uppercase tracking-wider cursor-pointer disabled:cursor-not-allowed"
              >
                Retry
              </button>
            </div>
          )}

          {isLoading && (
            <div
              role="status"
              aria-live="polite"
              className="rounded-xl border border-[#D4AF37]/20 bg-[#D4AF37]/[0.05] px-3 py-2 text-[10px] text-[#D4AF37] font-bold uppercase tracking-wider"
            >
              AURIX AI is analyzing your enterprise context...
            </div>
          )}
          <form
            onSubmit={(event) => {
              event.preventDefault();
              onSubmitQuery();
            }}
            className="flex items-center gap-2"
          >
            <input
              type="text"
              value={queryText}
              onChange={(event) =>
                onQueryTextChange(event.target.value)
              }
              placeholder="Ask contextual questions about this workbench..."
              className="flex-1 bg-[#15171A] border border-white/15 rounded-lg px-3 py-2 text-white text-xs placeholder-slate-500 focus:outline-none focus:border-[#D4AF37]"
            />

            <AurixButton
              variant="gold"
              size="md"
              type="submit"
              loading={isLoading}
            >
              <Send className="w-3.5 h-3.5" />
            </AurixButton>
          </form>
        </div>
      </div>
    </div>
  );
};
