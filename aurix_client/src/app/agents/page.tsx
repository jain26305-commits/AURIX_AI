"use client";

import React, { useState } from "react";
import { SubNav } from "@/components/shell/SubNav";
import { MetricCard } from "@/components/drawers/cards/MetricCard";
import { DataTable } from "@/components/ui/DataTable";
import Link from "next/link";

export default function AgentsWorkspace() {
  const [activeTab, setActiveTab] = useState("overview");
  const tabs = [
    { id: "overview", label: "Agent Overview" },
    { id: "executions", label: "Journal Executions" },
    { id: "approvals", label: "Pending Approvals" },
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center border-b border-slate-800/80 pb-3">
        <div>
          <h1 className="text-2xl font-bold font-display text-white">Governed Autonomous Agents</h1>
          <p className="text-xs text-slate-400 mt-0.5">Execution plane monitoring & Agent Studio control center</p>
        </div>
        <Link
          href="/agent-studio"
          className="px-4 py-2 bg-gold hover:bg-gold rounded-xl text-xs font-bold text-white transition shadow-lg"
        >
          Open Visual Agent Studio ➔
        </Link>
      </div>

      <SubNav tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <MetricCard title="Active Governed Agents" value={4} statusColor="gold" />
        <MetricCard title="Autonomous Success Rate" value={97.6} suffix="%" statusColor="success" />
        <MetricCard title="Verified Value Attributed" value={84500} prefix="$" statusColor="neutral" />
      </div>

      <DataTable
        columns={[
          { key: "agentId", header: "Agent ID" },
          { key: "name", header: "Agent Name" },
          { key: "type", header: "Specialization Archetype" },
          { key: "risk", header: "Risk Level" },
          { key: "status", header: "Status" },
        ]}
        data={[
          { agentId: "AGT-FIN-01", name: "Working Capital & Finance Agent", type: "FINANCE_AGENT", risk: "MEDIUM", status: "ACTIVE" },
          { agentId: "AGT-PROC-01", name: "Procurement & Supplier Agent", type: "PROCUREMENT_AGENT", risk: "HIGH", status: "ACTIVE" },
        ]}
      />
    </div>
  );
}
