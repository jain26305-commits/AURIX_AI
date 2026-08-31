'use client';

import React, { useEffect } from 'react';
import { useParams } from 'next/navigation';
import { SkuBreadcrumbBar } from '@/components/navigation/SkuBreadcrumbBar';
import { SkuSummaryHeader } from '@/components/features/workspace/SkuSummaryHeader';
import { SkuIntelligenceTabs } from '@/components/features/workspace/SkuIntelligenceTabs';
import { useSkuWorkspace } from '@/hooks/useSkuWorkspace';


import { useWorkspaceHeader } from '@/context/WorkspaceHeaderContext';
import { useSkuWorkspaceContext } from '@/context/SkuWorkspaceContext';

export default function SkuWorkspacePage() {
  const params = useParams();
  const rawId = params?.id;
  const skuId = typeof rawId === 'string' ? rawId : Array.isArray(rawId) ? rawId[0] : 'SKU-001';
  const { setSelectedSkuId, availableSkus } = useSkuWorkspaceContext();

  useEffect(() => {
    if (!availableSkus.some((sku) => sku.id === skuId)) {
      return undefined;
    }

    const frame = window.requestAnimationFrame(() => {
      setSelectedSkuId(skuId);
    });

    return () => {
      window.cancelAnimationFrame(frame);
    };
  }, [availableSkus, setSelectedSkuId, skuId]);

  const { story, loading, activeTab, setActiveTab } = useSkuWorkspace(skuId);

  useWorkspaceHeader({ activeWorkspaceTitle: "SKU Workspace", activeSku: story?.skuId });

  if (loading || !story) {
    return (
      <>
        <div className="py-24 flex flex-col items-center justify-center text-center space-y-4">
          <div className="w-8 h-8 rounded-full border-2 border-gold border-t-transparent animate-spin" />
          <p className="text-xs font-mono text-slate-400 tracking-widest uppercase">
            COMPILING 360Â° SKU INTELLIGENCE PROFILE...
          </p>
        </div>
      </>
    );
  }

  return (
    <>
      <div className="space-y-6 animate-pure-fade">
        {/* Top Breadcrumbs & Rapid Switcher */}
        <SkuBreadcrumbBar
          skuId={story.skuId}
          skuName={story.skuName}
          category={story.category}
          healthStatus={story.overallHealthStatus}
        />

        {/* Master Synthesis Header */}
        <SkuSummaryHeader story={story} />

        {/* Multi-Domain Interactive Tabs */}
        <SkuIntelligenceTabs story={story} activeTab={activeTab} onTabChange={setActiveTab} />
      </div>
    </>
  );
}
