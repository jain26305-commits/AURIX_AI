'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { FileDropZone } from '@/components/features/data-intake/FileDropZone';
import { UploadPipelineStatus } from '@/components/features/data-intake/UploadPipelineStatus';
import { SchemaMapperGrid } from '@/components/features/data-intake/SchemaMapperGrid';
import { DataInspectionPreview } from '@/components/features/data-intake/DataInspectionPreview';
import { IntakeValidationSummary } from '@/components/features/data-intake/IntakeValidationSummary';
import { useDataIntake } from '@/hooks/useDataIntake';
import { IntakeService } from '@/services/api/intakeService';
import { AurixButton } from '@/components/ui/AurixButton';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { AurixCard } from '@/components/ui/AurixCard';
import { Building2, Server, UploadCloud, Layers, ArrowRight, ArrowLeft, Sparkles, ShieldCheck, RotateCcw, Radio, FileSpreadsheet } from 'lucide-react';
import { useWorkspaceHeader } from '@/context/WorkspaceHeaderContext';

type OnboardingStep = 'ORG_PROFILE' | 'SYSTEM_SELECTION' | 'DATA_INGEST' | 'SCHEMA_MAPPING' | 'CAPABILITY_GATES';

interface SystemOption {
  id: string;
  name: string;
  category: 'ERP' | 'WMS' | 'TMS' | 'RAW';
  deployment: 'Cloud API' | 'Local Agent (Outbound HTTPS)' | 'Direct Ingest';
  syncLatency: string;
  supported: boolean;
}

const AVAILABLE_SYSTEMS: SystemOption[] = [
  { id: 'SYS-TALLY', name: 'Tally Prime / ERP 9', category: 'ERP', deployment: 'Local Agent (Outbound HTTPS)', syncLatency: 'Near Real-Time CDC', supported: true },
  { id: 'SYS-ODOO', name: 'Odoo Enterprise (v16/v17/v18)', category: 'ERP', deployment: 'Cloud API', syncLatency: 'Every 5 mins', supported: true },
  { id: 'SYS-SAP', name: 'SAP S/4HANA / ECC', category: 'ERP', deployment: 'Cloud API', syncLatency: 'Real-Time Webhooks', supported: true },
  { id: 'SYS-WMS', name: 'Manhattan Associates / Custom WMS', category: 'WMS', deployment: 'Cloud API', syncLatency: 'Instantaneous', supported: true },
  { id: 'SYS-TMS', name: 'Freight Carrier TMS & GPS Listener', category: 'TMS', deployment: 'Cloud API', syncLatency: 'Every 15 mins', supported: true },
  { id: 'SYS-RAW', name: 'Flat File Data Lake (CSV / Parquet)', category: 'RAW', deployment: 'Direct Ingest', syncLatency: 'Batch On-Demand', supported: true },
];

export default function DataIntakePage() {
  useWorkspaceHeader({ activeWorkspaceTitle: "Data Intake & Onboarding" });
  const router = useRouter();
  const [activeStep, setActiveStep] = useState<OnboardingStep>('ORG_PROFILE');
  const [isCommitting, setIsCommitting] = useState(false);

  // Organization Metadata State
  const [orgData, setOrgData] = useState({
    legalName: 'Quidch Apparel Private Limited',
    industry: 'Apparel, Garments & Textile Manufacturing',
    operatingCountry: 'India (Domestic & Export)',
    skuCountEstimate: '2,500+ Active SKUs',
    primaryDistributionHub: 'Bengaluru DC & Tiruppur Production Facility',
  });

  // Selected Systems State
  const [selectedSystems, setSelectedSystems] = useState<string[]>(['SYS-RAW', 'SYS-TALLY', 'SYS-WMS']);

  const {
    stage,
    progressPercent,
    metadata,
    mappings,
    previewRows,
    validationIssues,
    processUploadedFile,
    updateColumnMapping,
    resetIntake,
  } = useDataIntake();

  const handleSystemToggle = (sysId: string) => {
    setSelectedSystems((prev) =>
      prev.includes(sysId) ? prev.filter((id) => id !== sysId) : [...prev, sysId]
    );
  };

  const handleCommit = async () => {
    if (!metadata?.fileId) {
      return;
    }

    setIsCommitting(true);

    try {
      const committed = await IntakeService.commitMappings(
        metadata.fileId,
        mappings,
      );

      if (committed) {
        setActiveStep('CAPABILITY_GATES');
      }
    } catch (error) {
      console.error('[DataIntake] Failed to commit mappings:', error);
    } finally {
      setIsCommitting(false);
    }
  };

  const rawColumns = previewRows.length > 0 ? Object.keys(previewRows[0]) : [];

  return (
    <>
      <div className="space-y-8 font-mono select-none">
        {/* Workspace Top Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2 py-0.5 rounded bg-gold/10 border border-gold/30 text-gold text-[10px] font-bold tracking-widest uppercase">
                ENTERPRISE ONBOARDING
              </span>
              <span className="text-slate-500 text-xs">• DATA INTAKE PIPELINE</span>
            </div>
            <h1 className="text-xl font-bold text-white tracking-wide">OPERATIONAL DATA INTAKE & CONNECTIVITY</h1>
            <p className="text-xs text-slate-400 mt-0.5">
              Establish enterprise organizational context, link ERP/WMS/TMS data connectors, and unlock capability modules.
            </p>
          </div>

          <div className="flex items-center gap-2">
            {stage !== 'idle' && (
              <AurixButton variant="ghost" size="sm" onClick={resetIntake}>
                <RotateCcw className="w-3.5 h-3.5 mr-1.5" /> RESET UPLOAD
              </AurixButton>
            )}
          </div>
        </div>

        {/* 5-Step Process Ribbon */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-2 p-1.5 bg-[#0C0E12] border border-white/[0.08] rounded-xl text-xs">
          {[
            { id: 'ORG_PROFILE', label: '1. Org Profile', icon: Building2 },
            { id: 'SYSTEM_SELECTION', label: '2. Systems & ERP', icon: Server },
            { id: 'DATA_INGEST', label: '3. Data Ingestion', icon: UploadCloud },
            { id: 'SCHEMA_MAPPING', label: '4. Validation & Schema', icon: Layers },
            { id: 'CAPABILITY_GATES', label: '5. Capability Gates', icon: Sparkles },
          ].map((s) => {
            const Icon = s.icon;
            const isActive = activeStep === s.id;
            return (
              <button
                key={s.id}
                onClick={() => setActiveStep(s.id as OnboardingStep)}
                className={`flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg font-bold transition-all cursor-pointer ${
                  isActive
                    ? 'bg-white/[0.08] text-white border border-white/20 shadow-[0_0_12px_rgba(212,175,55,0.12)]'
                    : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-gold' : 'text-slate-600'}`} />
                <span className="truncate">{s.label}</span>
              </button>
            );
          })}
        </div>

        {/* STEP 1: ORGANIZATION PROFILE */}
        {activeStep === 'ORG_PROFILE' && (
          <div className="space-y-6 animate-pure-fade">
            <AurixCard title="ENTERPRISE CONTEXT & OPERATIONAL PROFILE" badge={<AurixBadge variant="gold">STEP 01</AurixBadge>}>
              <p className="text-xs text-slate-400 mb-6">
                Define the structural operating profile of your enterprise so AURIX can tailor demand forecasting horizons, multi-echelon inventory policies, and lead-time models.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div className="space-y-1.5">
                  <label className="text-[10px] text-slate-400 font-bold uppercase">Enterprise Legal Entity</label>
                  <input
                    type="text"
                    value={orgData.legalName}
                    onChange={(e) => setOrgData({ ...orgData, legalName: e.target.value })}
                    className="w-full bg-[#15171A] border border-white/10 rounded-lg px-3 py-2 text-white font-mono focus:outline-none focus:border-[#D4AF37]"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-[10px] text-slate-400 font-bold uppercase">Industry Domain</label>
                  <input
                    type="text"
                    value={orgData.industry}
                    onChange={(e) => setOrgData({ ...orgData, industry: e.target.value })}
                    className="w-full bg-[#15171A] border border-white/10 rounded-lg px-3 py-2 text-white font-mono focus:outline-none focus:border-[#D4AF37]"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-[10px] text-slate-400 font-bold uppercase">Operating Geography</label>
                  <input
                    type="text"
                    value={orgData.operatingCountry}
                    onChange={(e) => setOrgData({ ...orgData, operatingCountry: e.target.value })}
                    className="w-full bg-[#15171A] border border-white/10 rounded-lg px-3 py-2 text-white font-mono focus:outline-none focus:border-[#D4AF37]"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-[10px] text-slate-400 font-bold uppercase">Catalog Scale (Active SKUs)</label>
                  <input
                    type="text"
                    value={orgData.skuCountEstimate}
                    onChange={(e) => setOrgData({ ...orgData, skuCountEstimate: e.target.value })}
                    className="w-full bg-[#15171A] border border-white/10 rounded-lg px-3 py-2 text-white font-mono focus:outline-none focus:border-[#D4AF37]"
                  />
                </div>
              </div>

              <div className="mt-4 space-y-1.5 text-xs">
                <label className="text-[10px] text-slate-400 font-bold uppercase">Primary Fulfillment & Manufacturing Hubs</label>
                <input
                  type="text"
                  value={orgData.primaryDistributionHub}
                  onChange={(e) => setOrgData({ ...orgData, primaryDistributionHub: e.target.value })}
                  className="w-full bg-[#15171A] border border-white/10 rounded-lg px-3 py-2 text-white font-mono focus:outline-none focus:border-[#D4AF37]"
                />
              </div>

              <div className="pt-6 mt-6 border-t border-white/[0.06] flex justify-end">
                <AurixButton variant="primary" onClick={() => setActiveStep('SYSTEM_SELECTION')}>
                  <span>CONFIRM PROFILE & SELECT SYSTEMS</span>
                  <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
                </AurixButton>
              </div>
            </AurixCard>
          </div>
        )}

        {/* STEP 2: SYSTEM SELECTION */}
        {activeStep === 'SYSTEM_SELECTION' && (
          <div className="space-y-6 animate-pure-fade">
            <AurixCard title="ACTIVE ENTERPRISE SYSTEMS & ERP CONNECTORS" badge={<AurixBadge variant="gold">STEP 02</AurixBadge>}>
              <p className="text-xs text-slate-400 mb-6">
                Select the systems currently operating across your supply chain. AURIX supports direct cloud APIs, local outbound HTTPS agents for on-premise Tally/Odoo, and flat files.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {AVAILABLE_SYSTEMS.map((sys) => {
                  const isSelected = selectedSystems.includes(sys.id);
                  return (
                    <div
                      key={sys.id}
                      onClick={() => handleSystemToggle(sys.id)}
                      className={`p-4 rounded-xl border transition-all cursor-pointer ${
                        isSelected
                          ? 'bg-gold/[0.04] border-gold/40 shadow-[0_0_12px_rgba(212,175,55,0.08)]'
                          : 'bg-white/[0.02] border-white/[0.06] hover:border-white/15'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-2.5">
                          <div className={`p-2 rounded-lg border ${isSelected ? 'bg-gold/10 border-gold/30 text-gold' : 'bg-white/[0.04] border-white/10 text-slate-500'}`}>
                            <Server className="w-4 h-4" />
                          </div>
                          <div>
                            <h4 className="text-xs font-bold text-white leading-tight">{sys.name}</h4>
                            <span className="text-[10px] text-slate-500">{sys.category} • {sys.deployment}</span>
                          </div>
                        </div>

                        <AurixBadge variant={isSelected ? 'success' : 'neutral'}>
                          {isSelected ? 'SELECTED' : 'AVAILABLE'}
                        </AurixBadge>
                      </div>

                      <div className="mt-3 pt-3 border-t border-white/[0.04] flex items-center justify-between text-[10px] text-slate-400">
                        <span className="flex items-center gap-1">
                          <Radio className={`w-3 h-3 ${isSelected ? 'text-[#3DDB91] animate-pulse' : 'text-slate-600'}`} />
                          <span>Sync Latency: {sys.syncLatency}</span>
                        </span>
                        <span className="text-gold font-bold">READY TO LINK</span>
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="pt-6 mt-6 border-t border-white/[0.06] flex items-center justify-between">
                <AurixButton variant="ghost" onClick={() => setActiveStep('ORG_PROFILE')}>
                  <ArrowLeft className="w-3.5 h-3.5 mr-1.5" /> BACK
                </AurixButton>
                <AurixButton variant="primary" onClick={() => setActiveStep('DATA_INGEST')}>
                  <span>PROCEED TO DATA INGESTION</span>
                  <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
                </AurixButton>
              </div>
            </AurixCard>
          </div>
        )}

        {/* STEP 3: DATA INGESTION (FILE OR AGENT) */}
        {activeStep === 'DATA_INGEST' && (
          <div className="space-y-6 animate-pure-fade">
            <AurixCard title="DATA STREAM INGESTION & BATCH UPLOAD" badge={<AurixBadge variant="gold">STEP 03</AurixBadge>}>
              <p className="text-xs text-slate-400 mb-6">
                Upload historical demand orders, stock on hand, purchase orders, or BOM manifests. AURIX will automatically parse and detect schema structures.
              </p>

              {stage === 'idle' && (
                <div className="max-w-2xl mx-auto py-4">
                  <FileDropZone onFileSelected={processUploadedFile} />
                </div>
              )}

              {stage !== 'idle' && (
                <div className="space-y-6">
                  <UploadPipelineStatus stage={stage} progressPercent={progressPercent} />
                  <div className="flex justify-end">
                    <AurixButton variant="primary" onClick={() => setActiveStep('SCHEMA_MAPPING')}>
                      <span>INSPECT SCHEMA & VALIDATE</span>
                      <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
                    </AurixButton>
                  </div>
                </div>
              )}
            </AurixCard>
          </div>
        )}

        {/* STEP 4: SCHEMA MAPPING & PREVIEW */}
        {activeStep === 'SCHEMA_MAPPING' && (
          <div className="space-y-6 animate-pure-fade">
            <UploadPipelineStatus stage={stage} progressPercent={progressPercent} />

            {metadata && (
              <>
                <SchemaMapperGrid
                  mappings={mappings}
                  availableRawColumns={rawColumns}
                  onMappingChange={updateColumnMapping}
                />

                <DataInspectionPreview metadata={metadata} rows={previewRows} />

                <IntakeValidationSummary
                  issues={validationIssues}
                  isReady={stage === 'ready'}
                  onCommit={handleCommit}
                  isSubmitting={isCommitting}
                />
              </>
            )}

            {!metadata && (
              <div className="text-center py-12 space-y-3">
                <FileSpreadsheet className="w-8 h-8 text-slate-600 mx-auto" />
                <p className="text-xs text-slate-400">No active file mapped yet. Return to Data Ingestion to load a dataset.</p>
                <AurixButton variant="secondary" size="sm" onClick={() => setActiveStep('DATA_INGEST')}>
                  <ArrowLeft className="w-3.5 h-3.5 mr-1.5" /> GO TO DATA INGEST
                </AurixButton>
              </div>
            )}
          </div>
        )}

        {/* STEP 5: CAPABILITY READINESS GATES */}
        {activeStep === 'CAPABILITY_GATES' && (
          <div className="space-y-6 animate-pure-fade">
            <AurixCard title="AURIX CAPABILITY READINESS ASSESSMENT" badge={<AurixBadge variant="success">EVALUATED</AurixBadge>}>
              <p className="text-xs text-slate-400 mb-6">
                Based on your committed schema mapping and connected systems, AURIX has calculated the active operational readiness across all platform modules.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[
                  { name: 'Demand Intelligence', status: 'READY', desc: 'Sufficient historical order records found to train XGBoost & SARIMA models.', path: '/supply-chain?subdomain=demand-forecast' },
                  { name: 'Multi-Echelon Inventory', status: 'READY', desc: 'On-hand stock and lead times mapped. Safety stock solvers active.', path: '/inventory' },
                  { name: 'Supplier Risk Scorecards', status: 'READY', desc: 'Vendor records and PO delivery dates reconciled with P95 quantiles.', path: '/supply-chain?subdomain=planning' },
                  { name: 'Logistics Corridors', status: 'READY', desc: 'Carrier transit manifests and dispatch timestamps verified.', path: '/logistics' },
                  { name: 'Inbound Procurement & 3WM', status: 'READY', desc: 'PO and invoice reconciliation matrices operational.', path: '/supply-chain/procurement' },
                  { name: 'Manufacturing & MRP', status: 'PARTIAL', desc: 'Bill of Materials detected; link work-center capacities for full MRP schedule.', path: '/supply-chain/manufacturing' },
                  { name: 'Outbound Fulfillment', status: 'READY', desc: 'Sales order book and real-time ATP promissory solvers ready.', path: '/supply-chain/fulfillment' },
                  { name: 'Reverse Logistics', status: 'READY', desc: 'RMA intake and defect disposition routing active.', path: '/supply-chain/returns' },
                  { name: 'Working Capital Economics', status: 'READY', desc: 'Holding drag (22%) and cash conversion cycle models unlocked.', path: '/decisions/finance' },
                ].map((mod) => (
                  <div key={mod.name} className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06] flex flex-col justify-between space-y-3">
                    <div>
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-xs font-bold text-white">{mod.name}</span>
                        <AurixBadge variant={mod.status === 'READY' ? 'success' : 'warning'}>
                          {mod.status}
                        </AurixBadge>
                      </div>
                      <p className="text-[11px] text-slate-400 leading-relaxed">{mod.desc}</p>
                    </div>

                    <button
                      onClick={() => router.push(mod.path)}
                      className="w-full text-center py-1.5 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] text-[10px] text-gold font-bold transition-all cursor-pointer"
                    >
                      OPEN WORKSPACE →
                    </button>
                  </div>
                ))}
              </div>

              <div className="pt-6 mt-6 border-t border-white/[0.06] flex items-center justify-between">
                <AurixButton variant="secondary" onClick={() => router.push('/data/quality')}>
                  <ShieldCheck className="w-3.5 h-3.5 mr-1.5 text-gold" />
                  <span>VIEW DATA QUALITY REPORT</span>
                </AurixButton>

                <AurixButton variant="primary" onClick={() => router.push('/control-tower')}>
                  <span>LAUNCH EXECUTIVE CONTROL TOWER</span>
                  <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
                </AurixButton>
              </div>
            </AurixCard>
          </div>
        )}
      </div>
    </>
  );
}