"use client";

import React from "react";

export interface NotificationDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export const NotificationDrawer: React.FC<NotificationDrawerProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  const notifications = [
    { id: "NT-1", title: "High-Risk Decision Pending Approval", time: "5m ago", type: "ALERT", tier: "HIGH" },
    { id: "NT-2", title: "Agent ST-AGT-PROC-01 Deployed to PROD", time: "1h ago", type: "DEPLOY", tier: "INFO" },
    { id: "NT-3", title: "Supplier Delay Signal Ingested: Port Rotterdam", time: "3h ago", type: "SIGNAL", tier: "MEDIUM" },
  ];

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-sm h-full bg-slate-900 border-l border-slate-800 p-6 flex flex-col justify-between shadow-2xl overflow-y-auto">
        <div className="space-y-4">
          <div className="flex justify-between items-center border-b border-slate-800 pb-3">
            <h3 className="font-bold text-white text-base">Alerts & System Feed</h3>
            <button onClick={onClose} className="text-slate-400 hover:text-white">✕</button>
          </div>

          <div className="space-y-3">
            {notifications.map((n) => (
              <div key={n.id} className="p-3.5 bg-slate-950 border border-slate-800 rounded-xl space-y-1 text-xs">
                <div className="flex justify-between items-center">
                  <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded font-bold ${
                    n.tier === "HIGH" ? "bg-[#FF6B6B]/15 text-[#FF6B6B]" : "bg-slate-800 text-slate-300"
                  }`}>
                    {n.type}
                  </span>
                  <span className="text-[10px] text-slate-500 font-mono">{n.time}</span>
                </div>
                <div className="text-slate-200 font-medium">{n.title}</div>
              </div>
            ))}
          </div>
        </div>

        <button onClick={onClose} className="w-full py-2 bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-white rounded-lg transition">
          Dismiss Feed
        </button>
      </div>
    </div>
  );
};
