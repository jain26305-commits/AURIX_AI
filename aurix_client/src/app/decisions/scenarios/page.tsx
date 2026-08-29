'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { ScenarioBuilderSidebar } from '@/components/features/scenarios/ScenarioBuilderSidebar';
import { WhatIfComparisonTable } from '@/components/features/scenarios/WhatIfComparisonTable';
import { PolicyImpactSummary } from '@/components/features/scenarios/PolicyImpactSummary';
import { useScenarioSimulator } from '@/hooks/useScenarioSimulator';
import { AurixButton } from '@/components/ui/AurixButton';
import { ArrowRight, RotateCw } from 'lucide-react';
import { useWorkspaceHeader } from '@/context/WorkspaceHeaderContext';

export default function ScenariosPage() {
  useWorkspaceHeader({ activeWorkspaceTitle: "Scenario Studio" });
  const router = useRouter();
  const {
    suite,
    loading,
    activeScenarioId,
    setActiveScenarioId,
    activeScenario,
    leadTimeDelta,
    setLeadTimeDelta,
    serviceLevelTarget,
    setServiceLevelTarget,
    demandSurge,
    setDemandSurge,
    isSimulating,
    runCustomWhatIf,
    reload,
  } = useScenarioSimulator();

  if (loading || !suite || !activeScenario) {
    return (
      <>
        <div className="py-24 flex flex-col items-center justify-center text-center space-y-4">
          <div className="w-8 h-8 rounded-full border-2 border-gold border-t-transparent animate-spin" />
          <p className="text-xs font-mono text-slate-400 tracking-widest uppercase">
            COMPUTING DETERMINISTIC SCENARIO TRADEOFFS...
          </p>
        </div>
      </>
    );
  }

  return (
    <>
      <div className="space-y-8 animate-pure-fade">
        {/* Workspace Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-white tracking-wide">WHAT-IF SCENARIO STUDIO</h1>
            <p className="text-xs font-mono text-slate-400 mt-1">
              Multi-branch policy simulation, lead-time stress testing, and ROI optimization.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <AurixButton variant="secondary" size="sm" onClick={reload}>
              <RotateCw className="w-3.5 h-3.5 mr-1.5" /> RESET BASELINE
            </AurixButton>
            <AurixButton variant="gold" size="sm" onClick={() => router.push('/decisions/recommendations')}>
              <span>AI RECOMMENDATIONS</span>
              <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
            </AurixButton>
          </div>
        </div>

        {/* 1. Primary Comparison Table */}
        <WhatIfComparisonTable
          baseScenario={suite.baseScenario}
          branches={suite?.simulatedBranches || []}
          activeScenarioId={activeScenarioId}
          onSelectScenario={setActiveScenarioId}
        />

        {/* 2. Analytical Dual Panel */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left: Interactive Parameter Studio (5 Cols) */}
          <div className="lg:col-span-5 space-y-6">
            <ScenarioBuilderSidebar
              leadTimeDelta={leadTimeDelta}
              onLeadTimeChange={setLeadTimeDelta}
              serviceLevelTarget={serviceLevelTarget}
              onServiceLevelChange={setServiceLevelTarget}
              demandSurge={demandSurge}
              onDemandSurgeChange={setDemandSurge}
              onRunSimulation={runCustomWhatIf}
              isSimulating={isSimulating}
            />
          </div>

          {/* Right: Selected Strategy Scorecard (7 Cols) */}
          <div className="lg:col-span-7 space-y-6">
            <PolicyImpactSummary scenario={activeScenario} />
          </div>
        </div>
      </div>
    </>
  );
}