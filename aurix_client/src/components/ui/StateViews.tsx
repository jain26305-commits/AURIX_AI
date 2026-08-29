"use client";

import React from "react";

export const LoadingStateView: React.FC<{ message?: string }> = ({
  message = "Loading Intelligence Telemetry...",
}) => (
  <div className="w-full h-64 flex flex-col items-center justify-center p-8 bg-slate-900/40 border border-slate-800/80 rounded-2xl animate-pulse">
    <div className="w-8 h-8 border-2 border-slate-300 border-t-transparent rounded-full animate-spin mb-4" />
    <div className="text-sm font-medium text-slate-300">{message}</div>
    <div className="text-xs text-slate-500 mt-1 font-mono">Resolving Tenant Context & Deterministic Models</div>
  </div>
);

export const EmptyStateView: React.FC<{
  title?: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
}> = ({
  title = "No Data Available",
  description = "No active records matching current filters were returned from the Data Fabric.",
  actionLabel,
  onAction,
}) => (
  <div className="w-full h-64 flex flex-col items-center justify-center p-8 bg-slate-900/30 border border-slate-800 rounded-2xl text-center">
    <div className="w-10 h-10 rounded-full bg-slate-800 flex items-center justify-center text-slate-400 mb-3">
      📊
    </div>
    <h4 className="text-base font-semibold text-white mb-1">{title}</h4>
    <p className="text-xs text-slate-400 max-w-sm mb-4">{description}</p>
    {actionLabel && onAction && (
      <button
        onClick={onAction}
        className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-white rounded-lg transition"
      >
        {actionLabel}
      </button>
    )}
  </div>
);

export const ErrorStateView: React.FC<{
  title?: string;
  errorMessage?: string;
  onRetry?: () => void;
}> = ({
  title = "Telemetry Resolution Failed",
  errorMessage = "An unexpected error occurred while communicating with the API Gateway.",
  onRetry,
}) => (
  <div className="w-full p-6 bg-[#FF6B6B]/10 border border-[#FF6B6B]/30 rounded-2xl flex flex-col items-center justify-center text-center">
    <div className="w-10 h-10 rounded-full bg-[#FF6B6B]/15 border border-[#FF6B6B]/40 flex items-center justify-center text-[#FF6B6B] mb-3">
      ⚠️
    </div>
    <h4 className="text-base font-semibold text-[#FF6B6B] mb-1">{title}</h4>
    <p className="text-xs text-slate-400 max-w-md mb-4 font-mono">{errorMessage}</p>
    {onRetry && (
      <button
        onClick={onRetry}
        className="px-4 py-2 bg-[#FF6B6B]/25 hover:bg-[#FF6B6B]/40 text-xs font-semibold text-white rounded-lg transition"
      >
        Retry Request
      </button>
    )}
  </div>
);
